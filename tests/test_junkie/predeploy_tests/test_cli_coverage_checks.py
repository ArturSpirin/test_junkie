from test_junkie.decorators import Suite, test
from tests.junkie_suites import cli_coverage_checks


@Suite()
class CliCoverageChecksSuite:

    @test(parameters=cli_coverage_checks.CHECKS)
    def cli_coverage_checks(self, parameter):
        parameter()
