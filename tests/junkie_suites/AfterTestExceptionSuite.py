from test_junkie.decorators import test, afterTest, Suite
from tests.junkie_suites.TestListener import TestListener


@Suite(retry=2, listener=TestListener)
class AfterTestExceptionSuite:

    @afterTest()
    def after_test(self):
        raise Exception("Exception in after test")

    @test(retry=2)
    def ignore_1(self):
        pass

    @test(retry=2)
    def ignore_2(self):
        pass
