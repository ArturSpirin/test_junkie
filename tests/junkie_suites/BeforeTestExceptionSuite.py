from test_junkie.decorators import test, beforeTest, Suite
from tests.junkie_suites.TestListener import TestListener


@Suite(retry=2, listener=TestListener)
class BeforeTestExceptionSuite:

    @beforeTest()
    def before_test(self):
        raise Exception("Exception in before test")

    @test(retry=2)
    def ignore_1(self):
        pass

    @test(retry=2)
    def ignore_2(self):
        pass
