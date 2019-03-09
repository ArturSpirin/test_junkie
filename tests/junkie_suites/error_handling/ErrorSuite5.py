from test_junkie.decorators import Suite, test, afterTest
from tests.junkie_suites.TestListener import TestListener


@Suite(listener=TestListener)
class ErrorSuite5:

    @afterTest()
    def after_test(self):
        raise Exception("Expected")

    @test()
    def test_1(self, parameter):
        pass
