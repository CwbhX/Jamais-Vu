import numpy

from pyfft.cuda import Plan
import pycuda.driver as cuda
from pycuda.tools import make_default_context
import pycuda.gpuarray as gpuarray


class GPU(object):

    def __init__(self):
        cuda.init()
        context = make_default_context()
        stream = cuda.Stream()
