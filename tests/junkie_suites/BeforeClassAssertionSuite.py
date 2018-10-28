from test_junkie.decorators import test, beforeClass, Suite


@Suite(retry=2)
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
