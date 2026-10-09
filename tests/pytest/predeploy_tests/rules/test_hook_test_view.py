from test_junkie.builder import Builder
from test_junkie.constants import TestCategory
from test_junkie.runner import Runner
from tests.junkie_suites import HookTestViewSuite as fixtures
from tests.junkie_suites.HookTestViewSuite import HookTestViewSuite, HookTestViewMutatorSuite, HookWithoutTestArgSuite, \
    HookTestViewThreadedSuite


def _run():
    del fixtures.SEEN[:]
    Runner([HookTestViewSuite]).run()
    return Builder.get_execution_roster().get(HookTestViewSuite)


def test_hooks_that_declare_test_receive_the_running_test():
    _run()
    before = [s for s in fixtures.SEEN if s[0] == "before"]
    names = sorted({s[1] for s in before})
    assert names == ["once", "per_account"]
    assert ("before", "per_account", ["ui"], "admin", True) in before
    assert ("before", "per_account", ["ui"], "viewer", True) in before
    assert ("before", "once", ["api"], None, False) in before  # runs once: suite_parameter is None


def test_after_test_receives_a_suite_view_too():
    _run()
    after = [s for s in fixtures.SEEN if s[0] == "after"]
    assert after and all(s[2] == "HookTestViewSuite" for s in after)


def test_changes_through_the_view_never_reach_the_live_test():
    suite = _run()
    live = {t.get_function_name(): t for t in suite.get_test_objects()}
    assert live["per_account"].get_tags() == ["ui"]
    assert live["once"].get_tags() == ["api"]
    assert "custom_flag" not in vars(live["per_account"])
    assert live["per_account"].get_meta(None, "admin")["name"] == "original"
    assert ("local", True) in fixtures.SEEN  # but assignments are readable on the view itself
    assert ("isinstance", False) not in fixtures.SEEN  # isinstance(test, TestObject) holds for the view


def test_view_does_not_break_meta_update_or_results():
    suite = _run()
    live = {t.get_function_name(): t for t in suite.get_test_objects()}
    assert live["per_account"].get_meta(None, "admin")["recorded"] == "admin"
    assert live["per_account"].get_status(None, "viewer") == TestCategory.SUCCESS
    assert live["once"].get_status(None, None) == TestCategory.SUCCESS


def test_calling_a_non_getter_fails_only_that_hook():
    Runner([HookTestViewMutatorSuite]).run()
    suite = Builder.get_execution_roster().get(HookTestViewMutatorSuite)
    assert len(suite.get_test_objects()) == 1  # the live suite kept its tests
    metrics = suite.get_test_objects()[0].metrics.get_metrics()["None"]["None"]
    assert metrics["status"] == TestCategory.ERROR
    assert "read-only view" in metrics["tracebacks"][-1]


def test_view_is_safe_while_other_threads_write_meta():
    Runner([HookTestViewThreadedSuite]).run(test_multithreading_limit=8)
    live = Builder.get_execution_roster().get(HookTestViewThreadedSuite).get_test_objects()[0]
    statuses = [live.get_status(p, None) for p in range(40)]
    assert statuses == [TestCategory.SUCCESS] * 40


def test_hooks_without_a_test_argument_are_unchanged():
    del HookWithoutTestArgSuite.CALLS[:]
    Runner([HookWithoutTestArgSuite]).run()
    assert HookWithoutTestArgSuite.CALLS == ["before"]
