from test_junkie.decorators import Suite, test, beforeTest
from tests.junkie_suites.TestListener import TestListener


@Suite(listener=TestListener)
class ErrorSuite4:

    @beforeTest()
    def before_test(self):
        raise Exception("Expected")

    @test()
    def test_1(self, parameter):
        pass
