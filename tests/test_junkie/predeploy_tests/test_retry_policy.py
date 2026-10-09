from test_junkie.decorators import Suite, test
from tests.junkie_suites import retry_policy_checks


@Suite()
class RetryPolicySuite:

    @test(parameters=retry_policy_checks.CHECKS)
    def retry_policy(self, parameter):
        parameter()
