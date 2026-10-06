from test_junkie.decorators import Suite, test
from tests.junkie_suites import cli_checks


@Suite()
class CliInProcessSuite:

    @test(parameters=cli_checks.CHECKS)
    def cli(self, parameter):
        parameter()
