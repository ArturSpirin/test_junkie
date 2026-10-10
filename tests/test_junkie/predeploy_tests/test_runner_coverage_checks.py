from test_junkie.decorators import Suite, test

from tests.junkie_suites import runner_coverage_checks


@Suite()
class RunnerCoverageChecksSuite:

    @test(parameters=runner_coverage_checks.CHECKS)
    def runner_coverage_checks(self, parameter):
        parameter()
