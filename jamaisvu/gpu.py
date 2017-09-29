import numpy

from pyfft.cuda import Plan
import pycuda.driver as cuda
from pycuda.tools import make_default_context
import pycuda.gpuarray as gpuarray


class GPU(object):

    def _next_greater_power_of_2(self, x):
        return 2**(x-1).bit_length()

    def _hanning(n, N):
        return 0.5*(1 - numpy.cos((2*n*numpy.pi) / (N-1)))

    def _window(data, windowType="hanning"):
        dataLength = len(data)
        result = numpy.array()

        # Only type of window support for now
        if windowType == "hanning":
            hanningArray = numpy.array()
            for n in range(0, dataLength):  # This range might be slightly off
                hanningArray.append(self._hanning(n, dataLength))

            # TODO: Perform CUDA vector multiply

            return result

        else:
            return None


    def __init__(self):
        cuda.init()
        self.context = make_default_context()
        self.stream = cuda.Stream()

    def fft(self, data, windowType="hanning" channels=2):  # Data must be of NPArray with type complex64
        resizeLength = self._next_greater_power_of_2(len(data))
        data.resize(resizeLength, channels)  # Resize to Length and Height by filling with 0s

        hannedData = self._window(data, windowType=windowType)  # Perform Hann function to our data

        plan = Plan((resizeLength, channels), stream=self.stream)  # Give data dimensions
        gpu_data = gpuarray.to_gpu(hannedData)  # Send data to GPU memory
        plan.execute(gpu_data)  # Execute FFT on that data

        fftResult = gpu_data.get()  # Retrieve computed data from GPU memory
        # self.context.pop()  # Release GPU

        # TODO: Normalise the data before returning it
        return numpy.split(fftResult, 2)[0]  # Return first half of our data (FFT Mirroring)


    def spectrogram(songdata, windowSize=8096):
        # TODO: Split data into bins
        # TODO: Recombine FFTs of bins with convolutions?
