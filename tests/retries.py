import pprint
import time

from test_junkie.decorators import Suite, test
from test_junkie.runner import Runner


@Suite(retry=2)
class RetryUseCases:

    @test(retry=2)
    def no_retry(self):
        pass

    @test(retry=2)
    def retry(self):
        assert True is False
