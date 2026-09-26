from test_junkie.decorators import Suite, test


@Suite()
class RerunSuite:

    @test(tags=["a"])
    def test_tagged_a(self):
        pass

    @test(tags=["b"])
    def test_tagged_b(self):
        pass
