from test_junkie.decorators import Suite, test
from tests.junkie_suites import console_checks


@Suite()
class ConsoleSuite:

    @test(parameters=console_checks.CHECKS)
    def console(self, parameter):
        parameter()
