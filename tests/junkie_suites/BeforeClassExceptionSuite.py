from test_junkie.decorators import test, beforeClass, Suite
from tests.junkie_suites.TestListener import TestListener


@Suite(retry=2, listener=TestListener)
class BeforeClassExceptionSuite:

    @beforeClass()
    def before_class(self):
        raise Exception("Exception in before class")

    @test(retry=2)  # Should not get to the test retry
    def ignore_1(self):
        pass

    @test(retry=2)  # Should not get to the test retry
    def ignore_2(self):
        pass
