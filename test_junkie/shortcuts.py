from test_junkie.console import capture_output, CapturedOutput  # noqa: F401 - public, used from tests
from test_junkie.errors import SkipTest


def skip(reason=None):
    raise SkipTest(reason)
