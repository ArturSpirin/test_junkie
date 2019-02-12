from test_junkie.decorators import GroupRules, beforeGroup, afterGroup
from test_junkie.objects import TestObject, SuiteObject
from test_junkie.rules import Rules


class TestRules(Rules):

    def __init__(self, **kwargs):

        Rules.__init__(self, **kwargs)

    def before_class(self):
        assert isinstance(self.kwargs.get("suite"), SuiteObject), "Suite Object must be passed to the before_test()"

    def before_test(self, **kwargs):
        assert isinstance(kwargs.get("test"), TestObject), "Test Object must be passed to the before_test()"
        assert isinstance(self.kwargs.get("suite"), SuiteObject), "Suite Object must be passed to the before_test()"

    def after_test(self, **kwargs):
        assert isinstance(kwargs.get("test"), TestObject), "Test Object must be passed to the before_test()"
        assert isinstance(self.kwargs.get("suite"), SuiteObject), "Suite Object must be passed to the before_test()"

    def after_class(self):
        assert isinstance(self.kwargs.get("suite"), SuiteObject), "Suite Object must be passed to the before_test()"

    @GroupRules()
    def group_rules(self):

        from tests.junkie_suites.AdvancedSuite import AdvancedSuite

        @beforeGroup([AdvancedSuite])
        def before_group():
            pass

        @afterGroup([AdvancedSuite])
        def after_group():
            raise Exception("Test exception")

        from tests.junkie_suites.IgnoreSuite import IgnoreSuiteBeforeGroupRule
        from tests.junkie_suites.IgnoreSuite import IgnoreSuiteBeforeGroupRule2

        @beforeGroup([IgnoreSuiteBeforeGroupRule, IgnoreSuiteBeforeGroupRule2])
        def before_group():
            assert True is False
