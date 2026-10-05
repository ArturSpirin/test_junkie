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
