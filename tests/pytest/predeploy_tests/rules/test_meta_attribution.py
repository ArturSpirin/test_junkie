from test_junkie.runner import Runner
from test_junkie.builder import Builder
from tests.junkie_suites.MetaAttributionSuite import MetaAttributionSuite

Runner([MetaAttributionSuite]).run()

live_test = Builder.get_execution_roster().get(MetaAttributionSuite).get_test_objects()[0]


def test_meta_update_through_a_helper_lands_on_the_calling_test():
    # Meta.update() called from _update_via_helper() must still update test_one, not get lost
    assert live_test.get_meta()["name"] == "updated via helper"
