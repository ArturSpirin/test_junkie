from test_junkie.decorators import Suite, test
from tests.junkie_suites import run_error_checks


@Suite()
class RunErrorsSuite:

    @test(parameters=run_error_checks.CHECKS)
    def run_errors(self, parameter):
        parameter()
