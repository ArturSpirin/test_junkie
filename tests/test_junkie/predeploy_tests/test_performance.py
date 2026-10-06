from test_junkie.decorators import Suite, test
from tests.junkie_suites import perf_checks


@Suite()
class PerformanceSuite:

    @test(parameters=perf_checks.CHECKS)
    def performance(self, parameter):
        parameter()
