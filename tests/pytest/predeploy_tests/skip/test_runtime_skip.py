"""
Full coverage for runtime skip via shortcuts.skip() / shortcuts.SkipTest.

Covered:
  - skip() raises SkipTest
  - reason is stored on the exception
  - no-reason defaults to None
  - test status recorded as SKIP, not FAIL or ERROR
  - other tests in the suite still run
  - mixed suite: correct SKIP and SUCCESS counts
  - no retries on runtime skip even when suite retry > 1
  - ON_SKIP event fires
  - ON_SUCCESS does NOT fire
  - ON_COMPLETE fires (ON_IN_PROGRESS was already emitted before body ran)
  - ON_IN_PROGRESS fires
  - runtime skip works per test-parameter
  - @afterTest and Rules.after_test run after a runtime skip, before ON_SKIP
  - @afterTest failing after a skip records ERROR, no ON_SKIP, no retry
  - @afterTest does not run after a failed @beforeTest
"""
from test_junkie.constants import TestCategory
from test_junkie.errors import SkipTest
from test_junkie.runner import Runner
from test_junkie.shortcuts import skip

from tests.junkie_suites.skip.RuntimeSkipSuites import (
    RuntimeSkipSuite,
    RuntimeSkipNoRetrySuite,
    RuntimeSkipMixedSuite,
    RuntimeSkipEventSuite, _events,
    RuntimeSkipWithParamsSuite,
    RuntimeSkipAfterTestSuite, _hooks,
    RuntimeSkipRulesAfterTestSuite,
    RuntimeSkipAfterTestFailsSuite,
    BeforeTestFailsSuite,
)


# ── SkipTest exception and skip() shortcut ────────────────────────────────────

def test_skip_raises_skip_test():
    raised = False
    try:
        skip()
    except SkipTest:
        raised = True
    assert raised


def test_skip_with_reason_stores_reason():
    try:
        skip("account not configured")
    except SkipTest as e:
        assert e.reason == "account not configured"
        return
    assert False, "SkipTest was not raised"


def test_skip_no_reason_defaults_to_none():
    try:
        skip()
    except SkipTest as e:
        assert e.reason is None
        return
    assert False, "SkipTest was not raised"


# ── status via aggregator ─────────────────────────────────────────────────────

def test_runtime_skip_records_skip_status():
    aggregator = Runner([RuntimeSkipSuite]).run()
    assert aggregator.get_basic_report()["tests"][TestCategory.SKIP] >= 1


def test_runtime_skip_does_not_count_as_failure():
    aggregator = Runner([RuntimeSkipSuite]).run()
    report = aggregator.get_basic_report()["tests"]
    assert report[TestCategory.FAIL] == 0
    assert report[TestCategory.ERROR] == 0


def test_runtime_skip_other_tests_still_run():
    aggregator = Runner([RuntimeSkipSuite]).run()
    report = aggregator.get_basic_report()["tests"]
    assert report[TestCategory.SUCCESS] == 1
    assert report[TestCategory.SKIP] == 1


def test_runtime_skip_mixed_suite_correct_counts():
    aggregator = Runner([RuntimeSkipMixedSuite]).run()
    report = aggregator.get_basic_report()["tests"]
    assert report[TestCategory.SKIP] == 2
    assert report[TestCategory.SUCCESS] == 2
    assert report[TestCategory.FAIL] == 0
    assert report[TestCategory.ERROR] == 0


# ── retry guard ───────────────────────────────────────────────────────────────

def test_runtime_skip_does_not_retry():
    RuntimeSkipNoRetrySuite.call_count = 0
    Runner([RuntimeSkipNoRetrySuite]).run()
    assert RuntimeSkipNoRetrySuite.call_count == 1


# ── event firing ─────────────────────────────────────────────────────────────

def test_runtime_skip_fires_on_skip_event():
    _events.clear()
    Runner([RuntimeSkipEventSuite]).run()
    assert "skip" in _events


def test_runtime_skip_does_not_fire_on_success():
    _events.clear()
    Runner([RuntimeSkipEventSuite]).run()
    assert "success" not in _events


def test_runtime_skip_fires_on_complete():
    _events.clear()
    Runner([RuntimeSkipEventSuite]).run()
    assert "complete" in _events


def test_runtime_skip_fires_on_in_progress():
    _events.clear()
    Runner([RuntimeSkipEventSuite]).run()
    assert "in_progress" in _events


# ── test parameters ───────────────────────────────────────────────────────────

def test_runtime_skip_with_test_parameters():
    aggregator = Runner([RuntimeSkipWithParamsSuite]).run()
    report = aggregator.get_basic_report()["tests"]
    assert report[TestCategory.SKIP] == 1
    assert report[TestCategory.SUCCESS] == 2


# ── afterTest after a runtime skip ────────────────────────────────────────────

def test_runtime_skip_runs_after_test():
    _hooks.clear()
    aggregator = Runner([RuntimeSkipAfterTestSuite]).run()
    assert _hooks == ["open", "close"]
    assert aggregator.get_basic_report()["tests"][TestCategory.SKIP] == 1


def test_runtime_skip_runs_rules_after_test():
    _hooks.clear()
    Runner([RuntimeSkipRulesAfterTestSuite]).run()
    assert _hooks == ["rules.after_test"]


def test_runtime_skip_after_test_runs_before_on_skip():
    _events.clear()
    Runner([RuntimeSkipEventSuite]).run()
    assert _events.index("after_test") < _events.index("skip")


def test_runtime_skip_after_test_fails_is_error_not_retried():
    _events.clear()
    RuntimeSkipAfterTestFailsSuite.call_count = 0
    aggregator = Runner([RuntimeSkipAfterTestFailsSuite]).run()
    report = aggregator.get_basic_report()["tests"]
    assert RuntimeSkipAfterTestFailsSuite.call_count == 1
    assert report[TestCategory.ERROR] == 1
    assert report[TestCategory.SKIP] == 0
    assert "skip" not in _events
    assert "error" in _events
    assert "complete" in _events


# ── failed beforeTest: afterTest does not run ─────────────────────────────────

def test_failed_before_test_does_not_run_after_test():
    _hooks.clear()
    aggregator = Runner([BeforeTestFailsSuite]).run()
    assert _hooks == ["open"]
    assert aggregator.get_basic_report()["tests"][TestCategory.ERROR] == 1
