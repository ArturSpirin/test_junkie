from test_junkie.builder import Builder
from test_junkie.decorators import Suite, test
from test_junkie.runner import Runner
from tests.junkie_suites.DeepCopySuite import DeepCopySuite
from tests.junkie_suites.MetaAttributionSuite import MetaAttributionSuite


@Suite()
class MetaAttributionTestSuite:

    @test()
    def meta_update_through_helper_lands_on_calling_test(self):
        Runner([MetaAttributionSuite]).run()
        live_test = Builder.get_execution_roster().get(MetaAttributionSuite).get_test_objects()[0]
        assert live_test.get_meta()["name"] == "updated via helper"


@Suite()
class RulesIndependentCopiesTestSuite:

    @test()
    def beforeClass_receives_independent_suite_copy(self):
        Runner([DeepCopySuite]).run()
        live_suite = Builder.get_execution_roster().get(DeepCopySuite)
        assert "mutated_by_rule" not in live_suite.get_kwargs()

    @test()
    def beforeTest_receives_independent_test_copy(self):
        Runner([DeepCopySuite]).run()
        live_suite = Builder.get_execution_roster().get(DeepCopySuite)
        live_test = live_suite.get_test_objects()[0]
        assert live_test.get_tags() == ["original"]

