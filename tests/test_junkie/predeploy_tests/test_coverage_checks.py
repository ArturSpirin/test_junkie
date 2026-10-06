from test_junkie.decorators import Suite, test
from tests.junkie_suites import coverage_checks


@Suite()
class CoverageChecksSuite:

    @test(parameters=coverage_checks.CHECKS)
    def coverage_checks(self, parameter):
        parameter()
