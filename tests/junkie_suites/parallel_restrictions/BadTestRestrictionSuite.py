from test_junkie.decorators import Suite, test


@Suite()
class BadTestRestrictionSuite:

    @test(pr=["not_a_function"])
    def a(self):
        pass
