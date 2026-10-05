from test_junkie.decorators import Suite, test
from tests.junkie_suites import RetrySetupTeardownSuite as fixture


@Suite()
class RetrySetupTeardownTestSuite:

    @test()
    def suite_retry_sets_up_and_tears_down_only_the_failed_suite_parameter(self):
        # the retry pass ran @beforeClass for the next suite parameter, found nothing left to retry and stopped -
        # skipping its @afterClass (a leaked browser/session per occurrence in UI suites)
        assert fixture.run() == fixture.EXPECTED_CALLS
