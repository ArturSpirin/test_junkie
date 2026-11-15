import re

from test_junkie.console import capture_output, CapturedOutput  # noqa: F401 - public, used from tests
from test_junkie.errors import SkipTest


def skip(reason=None):
    raise SkipTest(reason)


def raises(expected_exception, match=None):
    """
    Asserts that the block raises expected_exception (a class or a tuple of them).

        with raises(ValueError, match=r"bad id") as caught:
            parse("x")
        assert caught.value.args == ("bad id x",)

    The test FAILs (AssertionError) when nothing is raised, a different exception is raised,
    or match (a regex, checked with re.search against str(exception)) does not match.
    skip() and interrupts (KeyboardInterrupt, SystemExit) inside the block pass through untouched,
    unless their type is listed in expected_exception itself.
    :param expected_exception: exception class or tuple of exception classes
    :param match: optional regex string or compiled pattern
    :return: Raised context manager; after the block, .value is the exception and .type its class
    """
    return Raised(expected_exception, match)


class Raised(object):

    def __init__(self, expected_exception, match=None):
        expected = expected_exception if isinstance(expected_exception, tuple) else (expected_exception,)
        if not expected or not all(isinstance(e, type) and issubclass(e, BaseException) for e in expected):
            raise TypeError("raises() expects an exception class or a tuple of them, got {!r}"
                            .format(expected_exception))
        self.expected_exception = expected
        self.match = match
        self._value = None

    @property
    def value(self):
        if self._value is None:
            raise AttributeError("raises(): no exception was caught yet, read .value after the with block")
        return self._value

    @property
    def type(self):
        return type(self.value)

    def _expected_names(self):
        return " or ".join(e.__name__ for e in self.expected_exception)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            raise AssertionError("DID NOT RAISE {}".format(self._expected_names()))
        if exc is None:
            exc = exc_type()
        if issubclass(exc_type, SkipTest) and not any(issubclass(e, SkipTest) for e in self.expected_exception):
            return False  # runtime skip() still skips
        if issubclass(exc_type, self.expected_exception):
            if self.match is not None and not re.search(self.match, str(exc)):
                pattern = getattr(self.match, "pattern", self.match)
                raise AssertionError("{} message {!r} does not match {!r}"
                                     .format(exc_type.__name__, str(exc), pattern)) from exc
            self._value = exc
            return True
        if not issubclass(exc_type, Exception):
            return False  # KeyboardInterrupt, SystemExit, TestInterrupted still stop the run
        raise AssertionError("expected {}, got {}: {}"
                             .format(self._expected_names(), exc_type.__name__, exc)) from exc
