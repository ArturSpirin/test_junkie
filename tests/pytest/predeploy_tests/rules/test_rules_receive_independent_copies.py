from test_junkie.runner import Runner
from test_junkie.builder import Builder
from tests.junkie_suites.DeepCopySuite import DeepCopySuite

Runner([DeepCopySuite]).run()

live_suite = Builder.get_execution_roster().get(DeepCopySuite)
live_test = live_suite.get_test_objects()[0]


def test_before_class_receives_an_independent_suite_copy():
    # before_class() mutates the suite copy it's given - the live suite shouldn't see it
    assert "mutated_by_rule" not in live_suite.get_kwargs()


def test_before_test_receives_an_independent_test_copy():
    # before_test() mutates the test copy it's given - the live test's tags shouldn't change
    assert live_test.get_tags() == ["original"]
