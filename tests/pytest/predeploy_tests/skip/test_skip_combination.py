"""
skip= callables that declare parameter and/or suite_parameter (G5).

Covered:
  - suite_parameter only, parameter only, both, meta + suite_parameter, a bound method: only those combinations skip
  - meta-only and no-arg callables work as before
  - the callable is asked once per combination
  - a test that doesn't run per suite parameter is asked under the first suite parameter, and a skipped combination
    is never dispatched under a later one
  - a skipped combination is not retried, its body never runs
  - ON_SKIP reaches the listener with the combination
  - expected_units equals the results recorded
  - a suite skip= that declares suite_parameter raises BadParameters
"""
import pytest

from test_junkie.builder import Builder
from test_junkie.console import expected_units
from test_junkie.constants import TestCategory
from test_junkie.errors import BadParameters

from tests.junkie_suites import SkipCombinationSuite as fixture
from tests.junkie_suites.SkipCombinationSuite import SkipCombinationSuite, SuiteSkipPerCombinationSuite

SKIP, SUCCESS = TestCategory.SKIP, TestCategory.SUCCESS


def _statuses(test, params):
    return {(sp, p): test.get_status(p, sp) for sp in ["pg", "sqlite"] for p in params}


def test_suite_parameter_only():
    _, tests = fixture.run(SkipCombinationSuite)
    assert _statuses(tests["by_suite_parameter"], [None]) == {("pg", None): SUCCESS, ("sqlite", None): SKIP}


def test_parameter_only():
    _, tests = fixture.run(SkipCombinationSuite)
    assert _statuses(tests["by_parameter"], [1, 2]) == \
        {("pg", 1): SUCCESS, ("pg", 2): SKIP, ("sqlite", 1): SUCCESS, ("sqlite", 2): SKIP}


def test_both_skip_one_combination_asked_once_each():
    _, tests = fixture.run(SkipCombinationSuite)
    assert _statuses(tests["by_both"], [1, 2]) == \
        {("pg", 1): SUCCESS, ("pg", 2): SUCCESS, ("sqlite", 1): SUCCESS, ("sqlite", 2): SKIP}
    assert [c for c in fixture.CALLS if c[0] == "callable"] == \
        [("callable", "pg", 1), ("callable", "pg", 2), ("callable", "sqlite", 1), ("callable", "sqlite", 2)]
    assert ("by_both", "sqlite", 2) not in fixture.CALLS


def test_meta_and_suite_parameter():
    _, tests = fixture.run(SkipCombinationSuite)
    assert _statuses(tests["by_meta_and_suite_parameter"], [None]) == {("pg", None): SKIP, ("sqlite", None): SUCCESS}


def test_bound_method():
    _, tests = fixture.run(SkipCombinationSuite)
    assert _statuses(tests["by_method"], [None]) == {("pg", None): SKIP, ("sqlite", None): SUCCESS}


def test_meta_only_and_no_arg_callables_unchanged():
    _, tests = fixture.run(SkipCombinationSuite)
    assert tests["by_meta_only"].get_status(None, None) == SKIP
    assert ("by_meta_only", None, None) not in fixture.CALLS
    assert _statuses(tests["by_no_args"], [None]) == {("pg", None): SUCCESS, ("sqlite", None): SUCCESS}


def test_not_per_suite_parameter_asked_under_first_and_never_dispatched_later():
    _, tests = fixture.run(SkipCombinationSuite)
    assert tests["once"].get_status(1, None) == SUCCESS
    assert tests["once"].get_status(2, None) == SKIP
    assert [c for c in fixture.CALLS if c[0] == "once"] == [("once", "pg", 1), ("once", "pg", 2)]
    assert [c for c in fixture.CALLS if c[0] == "once_body"] == [("once_body", None, 1)]


def test_skipped_combination_not_retried():
    _, tests = fixture.run(SkipCombinationSuite)
    test = tests["skipped_and_flaky"]
    assert _statuses(test, [1, 2]) == {("pg", 1): SUCCESS, ("pg", 2): SKIP, ("sqlite", 1): SUCCESS, ("sqlite", 2): SKIP}
    bodies = [c for c in fixture.CALLS if c[0] == "skipped_and_flaky"]
    assert sorted(bodies) == [("skipped_and_flaky", "pg", 1)] * 2 + [("skipped_and_flaky", "sqlite", 1)] * 2
    assert test.is_qualified_for_retry(2, class_param="pg") is False
    assert test.is_qualified_for_retry(2, class_param="sqlite") is False


def test_on_skip_gets_the_combination():
    fixture.run(SkipCombinationSuite)
    for unit in [("by_suite_parameter", "sqlite", None), ("by_parameter", "pg", 2), ("by_parameter", "sqlite", 2),
                 ("by_both", "sqlite", 2), ("by_meta_and_suite_parameter", "pg", None), ("by_method", "pg", None),
                 ("once", None, 2), ("skipped_and_flaky", "pg", 2), ("skipped_and_flaky", "sqlite", 2)]:
        assert fixture.SKIPPED.count(unit) == 1, unit


def test_totals_and_expected_units():
    aggregator, _ = fixture.run(SkipCombinationSuite)
    report = aggregator.get_basic_report()["tests"]
    assert (report["total"], report[SUCCESS], report[SKIP]) == (23, 13, 10)
    assert report[TestCategory.FAIL] == 0 and report[TestCategory.ERROR] == 0
    assert expected_units(Builder.get_execution_roster().get(SkipCombinationSuite)) == report["total"]


def test_suite_skip_declaring_suite_parameter_raises():
    with pytest.raises(BadParameters, match="declare it on the test's skip=|Declare it on the test's skip="):
        fixture.run(SuiteSkipPerCombinationSuite)
    assert ("never_runs",) not in fixture.CALLS
