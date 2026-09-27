from test_junkie.decorators import Suite, test


@Suite(pr=["not_a_class"])
class BadSuiteRestriction:

    @test()
    def a(self):
        pass
