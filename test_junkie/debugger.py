import io
import logging
import sys
from contextlib import contextmanager


class LogJunkie:

    __LOGGER = None
    __ENABLED = False
    __PRIORITY = logging.ERROR
    __NAME = "TestJunkieLogger"
    __FORMAT = "%(asctime)s [%(levelname)s] (%(filename)s, %(funcName)s(), %(lineno)d - %(threadName)s) :: %(message)s"

    @staticmethod
    def enable_logging(level):

        LogJunkie.__ENABLED = True
        LogJunkie.__PRIORITY = level

    @staticmethod
    def disable_logging():

        LogJunkie.__ENABLED = False

    @staticmethod
    def __get_logger():

        if LogJunkie.__LOGGER is None:
            stderr_handler = logging.StreamHandler()
            stderr_handler.setFormatter(logging.Formatter(LogJunkie.__FORMAT))
            LogJunkie.__LOGGER = logging.getLogger(LogJunkie.__NAME)
            LogJunkie.__LOGGER.addHandler(stderr_handler)
            LogJunkie.__LOGGER.setLevel(LogJunkie.__PRIORITY)
        return LogJunkie.__LOGGER

    @staticmethod
    def info(msg):

        if LogJunkie.__ENABLED:
            LogJunkie.__get_logger().info(msg)

    @staticmethod
    def debug(msg):

        if LogJunkie.__ENABLED:
            LogJunkie.__get_logger().debug(msg)

    @staticmethod
    def error(msg, exc_info=False):

        if LogJunkie.__ENABLED:
            LogJunkie.__get_logger().error(msg, exc_info=exc_info)

    @staticmethod
    def warn(msg):

        if LogJunkie.__ENABLED:
            LogJunkie.__get_logger().warning(msg)


@contextmanager
def suppressed_stdout(suppress=False):
    if suppress:
        original_stdout = sys.stdout
        sys.stdout = io.StringIO()  # works with python 3
        original_level = logging.root.manager.disable
        logging.disable(logging.ERROR)
        try:
            yield
        finally:
            sys.stdout = original_stdout
            logging.disable(original_level)
    else:
        yield
