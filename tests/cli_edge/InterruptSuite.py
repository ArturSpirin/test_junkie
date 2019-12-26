from test_junkie.decorators import test, beforeClass
from test_junkie.decorators import Suite as Suite


@Suite()
class InterruptSuite:

    @beforeClass()
    def before_class(self):
        raise KeyboardInterrupt()

    @test()
    def interrupt(self):
        pass
