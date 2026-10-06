import os

from test_junkie.cli.cli_config import Config
from test_junkie.constants import CliConstants
from test_junkie.debugger import LogJunkie
from test_junkie.errors import BadParameters
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites import config_samples

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


def test_config_values_round_trip_with_their_types(tmp_path):
    # tj config update --html_report report.html used to make every tj run crash: values were saved with str()
    # and read back with ast.literal_eval, which raised ValueError on a bare report.html
    path = config_samples.make_config(str(tmp_path))
    config_samples.save(path, html_report="report.html", xml_report="reports/out.xml",
                        test_multithreading_limit=4, owners=["qa", "dev"], quiet=True, features=None)
    settings = config_samples.runtime_settings(path)
    assert settings.html_report == "report.html"
    assert settings.xml_report == "reports/out.xml"
    assert settings.test_thread_limit == 4
    assert settings.owners == ["qa", "dev"]
    assert settings.quiet is True
    assert settings.features is None


def test_configs_written_by_older_versions_still_load(tmp_path):
    path = config_samples.make_config(str(tmp_path), config_samples.LEGACY_LINES)
    settings = config_samples.runtime_settings(path)
    assert settings.html_report == "report.html"
    assert settings.xml_report == "reports/out.xml"
    # guess_root was read raw, so a saved False came back as the truthy string "False"
    assert config_samples.cli_runner(path).guess_root is False
