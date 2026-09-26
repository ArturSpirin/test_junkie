from test_junkie.decorators import Suite, test


@Suite()
class ReportFailureSuite:

    @test()
    def test_one(self):
        pass
