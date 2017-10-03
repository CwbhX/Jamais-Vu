import numpy
import pycuda.autoinit
import pycuda.driver as cuda
import pycuda.gpuarray as gpuarray

from pyfft.cuda import Plan
from pycuda.tools import make_default_context
from pycuda.compiler import SourceModule


class GPU(object):

    def _next_greater_power_of_2(self, x):
        return 2**(x-1).bit_length()

    def _hanning(n, N):
        return 0.5*(1 - numpy.cos((2*n*numpy.pi) / (N-1)))

    # returns the maximum of either minus or postive in a np array
    def _absmaxND(a, axis=None):  # From some stackoverflow question, cheers
        amax = a.max(axis)
        amin = a.min(axis)
        return np.where(-amin > amax, amin, amax)

    def _window(data, windowType="hanning"):
        binSize = len(data)
        threadLengthx = 0
        hannArray = []
        maxThreadSize = int(self.GPUAttributes[cuda.device_attribute.MAX_THREADS_PER_BLOCK])

        result = numpy.array()
        # Find the GPU thread size and number of blocks
        if binSize > maxThreadSize:
            gridOfBlocksx = int(binSize/maxThreadSize)
            threadLengthx = maxThreadSize
        else:
            threadLengthx = binSize
            gridOfBlocksx = 1

        channel1 = np.array(bin[:, 0]).astype(np.float32)  # Select appropriate channels
        channel2 = np.array(bin[:, 1]).astype(np.float32)

        channel1max = np.absolute(absmaxND(channel1))  # Find maximums for normalisation
        channel2max = np.absolute(absmaxND(channel2))

        for n in range(0, dataLength):  # This range might be slightly off
            hannArray.append(self._hanning(n, dataLength))

        hannNPArray = np.array(hannArray).astype(np.float32)
        product1 = np.zeros_like(channel1).astype(np.float32)
        product2 = np.zeros_like(channel1).astype(np.float32)

        # Channel 1
        self.vectorMultiplyMod(cuda.Out(product1), cuda.In(channel1), cuda.In(hannNPArray),
                                block=(threadLengthx,1,1), grid=(gridOfBlocksx,1))  # thread dimensions in a block, blocks in a grid
        # Channel 2
        self.vectorMultiplyMod(cuda.Out(product2), cuda.In(channel2), cuda.In(hannNPArray),
                        block=(threadLengthx,1,1), grid=(gridOfBlocksx,1))

        # TODO: Compile results into complex64 array for FFT

        return result



    def __init__(self, vmCFile):
        self.vectorMultiplyMod = SourceModule(open(vmCFile, "rt").read())  # Load C File vector multiplication kernel
        self.GPUAttributes = pycuda.autoinit.device.get_attributes()

    def fft(self, data, windowType="hanning", channels=2):  # Data must be of NPArray with type complex64
        resizeLength = self._next_greater_power_of_2(len(data))
        data.resize(resizeLength, channels)  # Resize to Length and Height by filling with 0s
        stream = cuda.Stream()
        context = make_default_context()

        hannedData = self._window(data, windowType=windowType)  # Perform Hann function to our data

        plan = Plan((resizeLength, channels), stream=stream)  # Give data dimensions
        gpu_data = gpuarray.to_gpu(hannedData)  # Send data to GPU memory
        plan.execute(gpu_data)  # Execute FFT on that data

        fftResult = gpu_data.get()  # Retrieve computed data from GPU memory
        context.pop()  # Release GPU

        # TODO: Normalise the data before returning it
        return numpy.split(fftResult, 2)[0]  # Return first half of our data (FFT Mirroring)


    def spectrogram(songdata, windowSize=8096):
        # TODO: Split data into bins
        # TODO: Recombine FFTs of bins with convolutions?
