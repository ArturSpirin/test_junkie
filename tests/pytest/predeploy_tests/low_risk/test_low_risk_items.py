import os

from test_junkie.cli.cli_config import Config
from test_junkie.constants import CliConstants
from test_junkie.debugger import LogJunkie
from test_junkie.errors import BadParameters
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager

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


def test_settings_only_report_kwargs_as_source_when_actually_passed():
    # PR #45 - a setting not passed to the Runner used to be logged as coming from KWARGS
    sources = QualityManager.setting_sources({"html_report": "report.html"})
    assert sources["html_report"] == "KWARGS"
    assert sources["test_multithreading_limit"] == "DEFAULTS"
    assert sources["suite_multithreading_limit"] == "DEFAULTS"


def test_test_junkie_home_env_var_overrides_root_dir(tmp_path):
    previous = os.environ.get(CliConstants.HOME_ENV_VAR)
    os.environ[CliConstants.HOME_ENV_VAR] = str(tmp_path)
    try:
        assert Config.get_root_dir() == str(tmp_path)
        assert Config.get_config_path(CliConstants.TJ_CONFIG_NAME).startswith(str(tmp_path))
    finally:
        if previous is None:
            del os.environ[CliConstants.HOME_ENV_VAR]
        else:
            os.environ[CliConstants.HOME_ENV_VAR] = previous
