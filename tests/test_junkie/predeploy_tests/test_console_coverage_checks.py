from test_junkie.decorators import Suite, test
from tests.junkie_suites import console_coverage_checks


@Suite()
class ConsoleCoverageChecksSuite:

    @test(parameters=console_coverage_checks.CHECKS)
    def console_coverage_checks(self, parameter):
        parameter()
