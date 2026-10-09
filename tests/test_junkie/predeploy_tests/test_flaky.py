from test_junkie.decorators import Suite, test
from tests.junkie_suites import flaky_checks


@Suite()
class FlakySuite:

    @test(parameters=flaky_checks.CHECKS)
    def flaky(self, parameter):
        parameter()
