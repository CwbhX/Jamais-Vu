import numpy, math, os
import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule

from reikna.cluda import dtypes, functions
from reikna.core import Computation, Transformation, Parameter, Annotation, Type
from reikna.fft import FFT
from reikna.algorithms import Transpose
import reikna.transformations as transformations

def hanning_window(arr, NFFT):
    """
    Applies the von Hann window to the rows of a 2D array.
    To account for zero padding (which we do not want to window), NFFT is provided separately.
    """
    if dtypes.is_complex(arr.dtype):
        coeff_dtype = dtypes.real_for(arr.dtype)
    else:
        coeff_dtype = arr.dtype
    return Transformation(
        [
            Parameter('output', Annotation(arr, 'o')),
            Parameter('input', Annotation(arr, 'i')),
        ],
        """
        ${dtypes.ctype(coeff_dtype)} coeff;
        %if NFFT != output.shape[0]:
        if (${idxs[1]} >= ${NFFT})
        {
            coeff = 1;
        }
        else
        %endif
        {
            coeff = 0.5 * (1 - cos(2 * ${numpy.pi} * ${idxs[-1]} / (${NFFT} - 1)));
        }
        ${output.store_same}(${mul}(${input.load_same}, coeff));
        """,
        render_kwds=dict(
            coeff_dtype=coeff_dtype, NFFT=NFFT,
            mul=functions.mul(arr.dtype, coeff_dtype)))

def rolling_frame(arr, NFFT, noverlap, pad_to):
    """
    Transforms a 1D array to a 2D array whose rows are
    partially overlapped parts of the initial array.
    """

    frame_step = NFFT - noverlap
    frame_num = (arr.size - noverlap) // frame_step
    frame_size = NFFT if pad_to is None else pad_to

    result_arr = Type(arr.dtype, (frame_num, frame_size))

    return Transformation(
        [
            Parameter('output', Annotation(result_arr, 'o')),
            Parameter('input', Annotation(arr, 'i')),
        ],
        """
        %if NFFT != output.shape[1]:
        if (${idxs[1]} >= ${NFFT})
        {
            ${output.store_same}(0);
        }
        else
        %endif
        {
            ${output.store_same}(${input.load_idx}(${idxs[0]} * ${frame_step} + ${idxs[1]}));
        }
        """,
        render_kwds=dict(frame_step=frame_step, NFFT=NFFT),
        # note that only the "store_same"-using argument can serve as a connector!
        connectors=['output'])

def crop_frequencies(arr):
    """
    Crop a 2D array whose columns represent frequencies to only leave the frequencies with
    different absolute values.
    """
    result_arr = Type(arr.dtype, (arr.shape[0], arr.shape[1] // 2 + 1))
    return Transformation(
        [
            Parameter('output', Annotation(result_arr, 'o')),
            Parameter('input', Annotation(arr, 'i')),
        ],
        """
        if (${idxs[1]} < ${input.shape[1] // 2 + 1})
            ${output.store_idx}(${idxs[0]}, ${idxs[1]}, ${input.load_same});
        """,
        # note that only the "load_same"-using argument can serve as a connector!
        connectors=['input'])

def getGridSize(blockDim, arrayDim):
	blockSize = 1
	arraySize = 1
	
	for dim in blockDim:
		blockSize *= dim
	
	for dim in arrayDim:
		arraySize *= dim
	
	grid1dim = int(math.ceil(math.sqrt(arraySize/blockSize)))
	if grid1dim < 1: # Prevent issue where we have a small array size
		grid1dim = 1
	
	return (grid1dim, grid1dim)

def maximum_filter_2d(arr2D, footprint): ## Make sure arr2D is our datatype float32 and footprint of int32
    arr2DMaxed = numpy.empty_like(arr2D)
    head, tail = os.path.split(os.path.abspath(__file__)) # Used so that we can always get the kernel which should be in the same directory as this file

    maxFunction = open(head + "/2DSlidingMaxFootprintKernel.c", "rt")
    maxFunction = SourceModule(maxFunction.read())
    slidingMaxKernel = maxFunction.get_function("slidingMaxiumum2D")

    blockSize = [16, 16] # To-do: Add a variable to this, can affect performance based on GPU
    gridSize = getGridSize(blockSize, arr2D.shape) # Get the size of our grid based on the size of a grid (blocksize)


    slidingMaxKernel(cuda.In(arr2D),                   # Input
                    cuda.Out(arr2DMaxed),              # Output
                    numpy.int32(footprint.shape[1]),   # Kernel Size
                    numpy.int32(arr2D.shape[1]),       # Row Stride
                    numpy.int32(1),                    # Column Stride
                    numpy.int32(int(arr2D.shape[1])),  # Array Column Count
                    numpy.int32(int(arr2D.shape[0])),  # Array Row Count
                    cuda.In(footprint),
                    block=(blockSize[0],blockSize[1],1),
                    grid=(gridSize[0],gridSize[1],1)
    )

    return arr2DMaxed

class Spectrogram(Computation):

    def __init__(self, x, NFFT=256, noverlap=128, pad_to=None, window=hanning_window):

        # print("x Data type = %s" % x.dtype)
        # print("Is Real = %s" % dtypes.is_real(x.dtype))
        # print("dim = %s" % x.ndim)
        assert dtypes.is_real(x.dtype)
        assert x.ndim == 1

        rolling_frame_trf = rolling_frame(x, NFFT, noverlap, pad_to)

        complex_dtype = dtypes.complex_for(x.dtype)
        fft_arr = Type(complex_dtype, rolling_frame_trf.output.shape)
        real_fft_arr = Type(x.dtype, rolling_frame_trf.output.shape)

        window_trf = window(real_fft_arr, NFFT)
        broadcast_zero_trf = transformations.broadcast_const(real_fft_arr, 0)
        to_complex_trf = transformations.combine_complex(fft_arr)
        amplitude_trf = transformations.norm_const(fft_arr, 1)
        crop_trf = crop_frequencies(amplitude_trf.output)

        fft = FFT(fft_arr, axes=(1,))
        fft.parameter.input.connect(
            to_complex_trf, to_complex_trf.output,
            input_real=to_complex_trf.real, input_imag=to_complex_trf.imag)
        fft.parameter.input_imag.connect(
            broadcast_zero_trf, broadcast_zero_trf.output)
        fft.parameter.input_real.connect(
            window_trf, window_trf.output, unwindowed_input=window_trf.input)
        fft.parameter.unwindowed_input.connect(
            rolling_frame_trf, rolling_frame_trf.output, flat_input=rolling_frame_trf.input)
        fft.parameter.output.connect(
            amplitude_trf, amplitude_trf.input, amplitude=amplitude_trf.output)
        fft.parameter.amplitude.connect(
            crop_trf, crop_trf.input, cropped_amplitude=crop_trf.output)

        self._fft = fft

        self._transpose = Transpose(fft.parameter.cropped_amplitude)

        Computation.__init__(self,
            [Parameter('output', Annotation(self._transpose.parameter.output, 'o')),
            Parameter('input', Annotation(fft.parameter.flat_input, 'i'))])

    def _build_plan(self, plan_factory, device_params, output, input_):
        plan = plan_factory()
        temp = plan.temp_array_like(self._fft.parameter.cropped_amplitude)
        plan.computation_call(self._fft, temp, input_)
        plan.computation_call(self._transpose, output, temp)
        return plan