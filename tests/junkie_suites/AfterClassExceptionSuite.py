from test_junkie.decorators import Suite, beforeClass, afterClass, test
from tests.junkie_suites.TestListener import TestListener


@Suite(retry=2, listener=TestListener)
class AfterClassExceptionSuite:

    @beforeClass()
    def before_class(self):
        pass

    @afterClass()
    def after_class(self):
        raise Exception("Exception Error in after class")

    @test(retry=2)
    def pass_1(self):
        pass

    @test(retry=2)
    def pass_2(self):
        pass
