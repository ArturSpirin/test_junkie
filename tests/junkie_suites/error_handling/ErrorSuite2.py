from test_junkie.decorators import Suite, test
from tests.junkie_suites.TestListener import TestListener


@Suite(listener=TestListener)
class ErrorSuite2:

    @test(parameters=[1, 2])
    def test_1(self):
        pass
