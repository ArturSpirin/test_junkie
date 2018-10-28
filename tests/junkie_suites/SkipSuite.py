from test_junkie.decorators import Suite, beforeClass, afterClass, test


@Suite(skip=True)
class SkipSuite:

    @beforeClass()
    def before_class(self):
        raise Exception("Exception in before class")

    @afterClass()
    def after_class(self):
        raise Exception("Exception in after class")

    @test()
    def pass_1(self):
        pass

    @test()
    def pass_2(self):
        pass
