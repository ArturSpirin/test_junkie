from test_junkie.debugger import LogJunkie
from test_junkie.errors import BadParameters
from test_junkie.runner import Runner

LogJunkie.enable_logging(10)

LogJunkie.debug("1")
LogJunkie.info("2")
LogJunkie.warn("3")
LogJunkie.error("4")
LogJunkie.disable_logging()


def test_bad_runner_initiation1():
    try:
        Runner(suites=None)
        raise AssertionError("Must have raised exception because bad args were passed in")
    except Exception as error:
        assert isinstance(error, BadParameters), "Type of exception is incorrect"
