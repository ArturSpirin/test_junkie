from test_junkie.decorators import Suite, test
from tests.junkie_suites import listener_error_checks


@Suite()
class ListenerErrorsSuite:

    @test(parameters=listener_error_checks.CHECKS)
    def listener_errors(self, parameter):
        parameter()
