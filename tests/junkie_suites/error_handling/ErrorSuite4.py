from test_junkie.decorators import Suite, test
from tests.junkie_suites.TestListener import TestListener
from tests.junkie_suites.error_handling.BadBeforeTestRules import BadBeforeTestRules


@Suite(listener=TestListener, rules=BadBeforeTestRules)
class ErrorSuite4:

    @test()
    def test_1(self, parameter):
        pass
