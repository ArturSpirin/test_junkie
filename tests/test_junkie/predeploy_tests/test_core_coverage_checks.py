from test_junkie.decorators import Suite, test
from tests.junkie_suites import core_coverage_checks


@Suite()
class CoreCoverageChecksSuite:

    @test(parameters=core_coverage_checks.CHECKS)
    def core_coverage_checks(self, parameter):
        parameter()
