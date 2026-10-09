from test_junkie.decorators import Suite, test
from tests.junkie_suites import param_key_checks


@Suite()
class ParamKeysSuite:

    @test(parameters=param_key_checks.CHECKS)
    def param_keys(self, parameter):
        parameter()
