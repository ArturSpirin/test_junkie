class TestJunkieExecutionError(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class TestListenerError(TestJunkieExecutionError):

    def __init__(self, message):
        TestJunkieExecutionError.__init__(self, message)


class ConfigError(TestJunkieExecutionError):

    def __init__(self, message):
        TestJunkieExecutionError.__init__(self, message)


class BadParameters(TestJunkieExecutionError):

    def __init__(self, message):
        TestJunkieExecutionError.__init__(self, message)


class BadCliParameters(TestJunkieExecutionError):

    def __init__(self, message):
        TestJunkieExecutionError.__init__(self, message)


class BadSignature(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class TestJunkieUsageError(Exception):
    """
    A Test Junkie API used where it can't work, e.g. Meta.update() with no running test. Not a
    TestJunkieExecutionError: raised in a test it fails that test (as an error) instead of stopping the run.
    """

    def __init__(self, message):
        Exception.__init__(self, message)


class SkipTest(Exception):

    def __init__(self, reason=None):
        Exception.__init__(self, reason)
        self.reason = reason
