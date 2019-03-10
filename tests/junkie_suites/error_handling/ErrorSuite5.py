from test_junkie.decorators import Suite, test
from tests.junkie_suites.TestListener import TestListener
from tests.junkie_suites.error_handling.BadAfterTestRules import BadAfterTestRules


@Suite(listener=TestListener, rules=BadAfterTestRules)
class ErrorSuite5:

    @test()
    def test_1(self, parameter):
        pass
