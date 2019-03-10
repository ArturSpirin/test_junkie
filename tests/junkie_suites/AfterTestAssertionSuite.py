from test_junkie.decorators import test, afterTest, Suite
from tests.junkie_suites.TestListener import TestListener


@Suite(retry=2, listener=TestListener)
class AfterTestAssertionSuite:

    @afterTest()
    def after_test(self):
        raise AssertionError("Assertion Error in before test")

    @test(retry=2)
    def ignore_1(self):
        pass

    @test(retry=2)
    def ignore_2(self):
        pass
