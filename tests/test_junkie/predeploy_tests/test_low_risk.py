from test_junkie.cli.cli_config import Config
from test_junkie.decorators import Suite, test
from test_junkie.errors import BadParameters
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager


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
