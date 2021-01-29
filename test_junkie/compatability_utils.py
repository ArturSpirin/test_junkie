import inspect
import sys


class CompatibilityUtils:

    def __init__(self):

        pass

    @staticmethod
    def getargspec(func):
        if CompatibilityUtils.in_python2():
            return inspect.getargspec(func)  # deprecated from Python 3.0
        return inspect.getfullargspec(func)

    @staticmethod
    def in_python2():
        return sys.version_info[0] < 3
