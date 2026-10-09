from test_junkie.decorators import Suite, test
from tests.junkie_suites import provider_checks


@Suite()
class ProviderFailuresSuite:

    @test(parameters=provider_checks.CHECKS)
    def provider_failures(self, parameter):
        parameter()
