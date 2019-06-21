# TODO overhaul errors and add documentation links


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
