from test_junkie.decorators import test, afterTest, Suite
from tests.junkie_suites.TestListener import TestListener


@Suite(retry=2, listener=TestListener)
class AfterTestSuite1:

    @afterTest()
    def after_test(self):
        raise AssertionError("Assertion Error in before class")

    @test(retry=2)
    def ignore_1(self):
        pass

    @test(retry=2)
    def ignore_2(self):
        pass


@Suite(retry=2, listener=TestListener)
class AfterTestSuite2:

    @afterTest()
    def after_test(self):
        raise Exception("Assertion Error in before class")

    @test(retry=2)
    def ignore_1(self):
        pass

    @test(retry=2)
    def ignore_2(self):
        pass
