from test_junkie.decorators import Suite, test


@Suite(retry=3)
class Retries:

    @test(retry_on=[Exception], retry=3)
    def retry_on_exception(self):

        raise Exception("Expected")

    @test(retry_on=[AssertionError], retry=3)
    def retry_on_assertion(self):
        assert True is False

    @test(no_retry_on=[Exception], retry=3)
    def no_retry_on_exception(self):
        raise Exception("Expected")

    @test(no_retry_on=[AssertionError], retry=3)
    def no_retry_on_assertion(self):
        assert True is False
