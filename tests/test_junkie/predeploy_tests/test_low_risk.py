from test_junkie.cli.cli_config import Config
from test_junkie.decorators import Suite, test
from test_junkie.errors import BadParameters
from test_junkie.runner import Runner


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
