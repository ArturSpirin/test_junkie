from test_junkie.errors import SkipTest


def skip(reason=None):
    raise SkipTest(reason)
