from test_junkie.decorators import test, beforeClass, Suite
from tests.junkie_suites.TestListener import TestListener


@Suite(retry=2, listener=TestListener)
class BeforeClassAssertionSuite:

    @beforeClass()
    def before_class(self):
        raise AssertionError("Assertion Error in before class")

    @test(retry=2)
    def ignore_1(self):
        pass

    @test(retry=2)
    def ignore_2(self):
        pass
