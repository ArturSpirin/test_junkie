from test_junkie.decorators import Suite, test
from tests.junkie_suites import group_rules_checks


@Suite()
class GroupRulesSuite:

    @test(parameters=group_rules_checks.CHECKS)
    def group_rules(self, parameter):
        parameter()
