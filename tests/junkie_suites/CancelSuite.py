import time

from test_junkie.decorators import Suite, beforeClass, afterClass, test, afterTest, beforeTest
from tests.junkie_suites.TestListener import TestListener


@Suite(listener=TestListener)
class CancelSuite:

    @beforeClass()
    def before_class(self):
        time.sleep(2)

    @afterClass()
    def after_class(self):
        pass

    @beforeTest()
    def before_test(self):
        pass

    @afterTest()
    def after_test(self):
        pass

    @test()
    def pass_1(self):
        pass

    @test()
    def pass_2(self):
        pass
