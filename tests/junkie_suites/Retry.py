from test_junkie.decorators import Suite, test
from tests.junkie_suites.Constants import Constants


@Suite(retry=3)
class Retries:

    @test(retry_on=[Exception], retry=3)
    def retry_on_exception(self):

        raise Constants.raise_large_exception()

    @test(retry_on=[AssertionError], retry=3)
    def retry_on_assertion(self):
        assert True is False

    @test(no_retry_on=[Exception], retry=3)
    def no_retry_on_exception(self):
        raise Constants.raise_large_exception()

    @test(no_retry_on=[AssertionError], retry=3)
    def no_retry_on_assertion(self):
        assert True is False
