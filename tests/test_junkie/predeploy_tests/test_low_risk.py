import os
import shutil
import tempfile

from test_junkie.cli.cli_config import Config
from test_junkie.constants import CliConstants
from test_junkie.decorators import Suite, test
from test_junkie.errors import BadParameters
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites import config_samples


@Suite()
class LowRiskItemsSuite:

    @test()
    def bad_runner_initiation_raises_bad_parameters(self):
        raised = False
        try:
            Runner(suites=None)
        except BadParameters:
            raised = True
        except Exception:
            raise AssertionError("Must raise BadParameters, not a different exception")
        assert raised

    @test()
    def cli_config_does_not_rely_on_appdirs_star_import(self):
        assert isinstance(Config.get_root_dir(), str)

    @test()
    def settings_only_report_kwargs_as_source_when_actually_passed(self):
        # PR #45 - a setting not passed to the Runner used to be logged as coming from KWARGS
        sources = QualityManager.setting_sources({"html_report": "report.html"})
        assert sources["html_report"] == "KWARGS"
        assert sources["test_multithreading_limit"] == "DEFAULTS"
        assert sources["suite_multithreading_limit"] == "DEFAULTS"

    @test()
    def test_junkie_home_env_var_overrides_root_dir(self):
        home = tempfile.mkdtemp()
        previous = os.environ.get(CliConstants.HOME_ENV_VAR)
        os.environ[CliConstants.HOME_ENV_VAR] = home
        try:
            assert Config.get_root_dir() == home
            assert Config.get_config_path(CliConstants.TJ_CONFIG_NAME).startswith(home)
        finally:
            if previous is None:
                del os.environ[CliConstants.HOME_ENV_VAR]
            else:
                os.environ[CliConstants.HOME_ENV_VAR] = previous
            os.rmdir(home)

    @test()
    def config_values_round_trip_with_their_types(self):
        directory = tempfile.mkdtemp()
        try:
            path = config_samples.make_config(directory)
            config_samples.save(path, html_report="report.html", xml_report="reports/out.xml",
                                test_multithreading_limit=4, owners=["qa", "dev"], quiet=True, features=None)
            settings = config_samples.runtime_settings(path)
            assert settings.html_report == "report.html"
            assert settings.xml_report == "reports/out.xml"
            assert settings.test_thread_limit == 4
            assert settings.owners == ["qa", "dev"]
            assert settings.quiet is True
            assert settings.features is None
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    @test()
    def configs_written_by_older_versions_still_load(self):
        directory = tempfile.mkdtemp()
        try:
            path = config_samples.make_config(directory, config_samples.LEGACY_LINES)
            settings = config_samples.runtime_settings(path)
            assert settings.html_report == "report.html"
            assert settings.xml_report == "reports/out.xml"
            assert config_samples.cli_runner(path).guess_root is False
        finally:
            shutil.rmtree(directory, ignore_errors=True)
