from test_junkie.cli.cli_config import Config
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


def test_cli_config_does_not_rely_on_the_appdirs_star_import():
    # cli_config.py used to only work because "from appdirs import *" happened to leak os/sys
    # into scope - it now imports what it needs directly
    assert isinstance(Config.get_root_dir(), str)
