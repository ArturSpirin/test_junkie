"""
Full coverage for the @Suite(order=) feature.

Covered:
  - TestOrder.ALPHABETICAL  : correct sequence, full set, no duplicates
  - TestOrder.PRIORITY_ASC  : correct sequence, full set, unprioritized last
  - TestOrder.PRIORITY_DESC : correct sequence, full set, unprioritized last, mirror of ASC
  - TestOrder.RANDOM        : full set, no duplicates, shuffle called, shuffle result respected
  - default (no order kwarg): identical to PRIORITY_ASC — proves zero regression
  - invalid order value     : BadParameters raised at run time
  - invalid order type      : BadParameters raised at decoration time
"""
from unittest.mock import patch

from test_junkie.errors import BadParameters
from test_junkie.runner import Runner

from tests.junkie_suites.ordering.OrderingSuites import (
    AlphaSuite, alpha_order,
    PriorityAscSuite, priority_asc_order,
    PriorityDescSuite, priority_desc_order,
    RandomSuite, random_order,
    DefaultSuite, default_order,
    InvalidValueSuite,
)

_DECLARATION_ORDER = ["test_a", "test_b", "test_c", "test_d", "test_e"]


# ── ALPHABETICAL ──────────────────────────────────────────────────────────────

def test_alpha_produces_alpha_sequence():
    alpha_order.clear()
    Runner([AlphaSuite]).run()
    assert alpha_order == ["test_apple", "test_banana", "test_mango", "test_zebra"]


def test_alpha_all_tests_execute():
    alpha_order.clear()
    Runner([AlphaSuite]).run()
    assert set(alpha_order) == {"test_apple", "test_banana", "test_mango", "test_zebra"}


def test_alpha_no_duplicates():
    alpha_order.clear()
    Runner([AlphaSuite]).run()
    assert len(alpha_order) == len(set(alpha_order))


# ── PRIORITY_ASC ──────────────────────────────────────────────────────────────

def test_priority_asc_produces_asc_sequence():
    priority_asc_order.clear()
    Runner([PriorityAscSuite]).run()
    assert priority_asc_order == ["test_high", "test_mid", "test_low", "test_unprioritized"]


def test_priority_asc_all_tests_execute():
    priority_asc_order.clear()
    Runner([PriorityAscSuite]).run()
    assert set(priority_asc_order) == {"test_high", "test_mid", "test_low", "test_unprioritized"}


def test_priority_asc_unprioritized_runs_last():
    priority_asc_order.clear()
    Runner([PriorityAscSuite]).run()
    assert priority_asc_order[-1] == "test_unprioritized"


# ── PRIORITY_DESC ─────────────────────────────────────────────────────────────

def test_priority_desc_produces_desc_sequence():
    priority_desc_order.clear()
    Runner([PriorityDescSuite]).run()
    assert priority_desc_order == ["test_low", "test_mid", "test_high", "test_unprioritized"]


def test_priority_desc_all_tests_execute():
    priority_desc_order.clear()
    Runner([PriorityDescSuite]).run()
    assert set(priority_desc_order) == {"test_high", "test_mid", "test_low", "test_unprioritized"}


def test_priority_desc_unprioritized_runs_last():
    priority_desc_order.clear()
    Runner([PriorityDescSuite]).run()
    assert priority_desc_order[-1] == "test_unprioritized"


def test_asc_and_desc_are_mirrors_of_each_other():
    priority_asc_order.clear()
    priority_desc_order.clear()
    Runner([PriorityAscSuite]).run()
    Runner([PriorityDescSuite]).run()
    asc_pri = [t for t in priority_asc_order if t != "test_unprioritized"]
    desc_pri = [t for t in priority_desc_order if t != "test_unprioritized"]
    assert asc_pri == list(reversed(desc_pri))


# ── RANDOM ────────────────────────────────────────────────────────────────────

def test_random_all_tests_execute():
    random_order.clear()
    Runner([RandomSuite]).run()
    assert set(random_order) == set(_DECLARATION_ORDER)


def test_random_no_duplicates():
    random_order.clear()
    Runner([RandomSuite]).run()
    assert len(random_order) == len(set(random_order))


def test_random_invokes_shuffle():
    random_order.clear()
    with patch("test_junkie.runner.random") as mock_random:
        mock_random.shuffle.side_effect = lambda lst: None  # no-op; keeps declaration order
        Runner([RandomSuite]).run()
    mock_random.shuffle.assert_called_once()


def test_random_respects_shuffle_result():
    """Patch shuffle to reverse the list — verifies TJ uses whatever shuffle produces.

    We capture the exact list shuffle receives rather than hardcoding declaration order,
    because prior Runner.__init__ calls may have already reordered the SuiteObject's
    internal test list via update_test_objects().
    """
    random_order.clear()
    captured = []

    def capture_and_reverse(lst):
        captured.extend(lst)
        lst.reverse()

    with patch("test_junkie.runner.random") as mock_random:
        mock_random.shuffle.side_effect = capture_and_reverse
        Runner([RandomSuite]).run()

    expected = [t.get_function_name() for t in reversed(captured)]
    assert random_order == expected


# ── DEFAULT (no order kwarg) — regression guard ───────────────────────────────

def test_default_order_matches_priority_asc():
    default_order.clear()
    Runner([DefaultSuite]).run()
    assert default_order == ["test_high", "test_mid", "test_low", "test_unprioritized"]


def test_default_all_tests_execute():
    default_order.clear()
    Runner([DefaultSuite]).run()
    assert set(default_order) == {"test_high", "test_mid", "test_low", "test_unprioritized"}


def test_default_unprioritized_runs_last():
    default_order.clear()
    Runner([DefaultSuite]).run()
    assert default_order[-1] == "test_unprioritized"


# ── INVALID ORDER VALUE ───────────────────────────────────────────────────────

def test_invalid_order_value_raises_bad_parameters():
    """A string that is not a recognised TestOrder constant must raise BadParameters.

    __prioritize is called in Runner.__init__, so the exception surfaces there.
    """
    raised = False
    try:
        Runner([InvalidValueSuite])
    except BadParameters as e:
        raised = True
        assert "banana" in str(e), "Error message should include the bad value"
        assert "order" in str(e).lower(), "Error message should mention the argument name"
    assert raised, "Expected BadParameters to be raised"


# ── INVALID ORDER TYPE ────────────────────────────────────────────────────────

def test_invalid_order_type_raises_bad_parameters_at_decoration_time():
    """Passing a non-string type for order= must raise BadParameters immediately."""
    from test_junkie.builder import Builder
    from test_junkie.decorators import Suite as TjSuite, test as tj_test

    raised = False
    try:
        @TjSuite(order=42)
        class _BadTypeSuite:
            @tj_test()
            def test_x(self): pass
    except BadParameters:
        raised = True
    finally:
        # Reset stale Builder state left by the failed @Suite decoration so that
        # any suites decorated after this point are not affected.
        Builder._Builder__set_current_suite_object_defaults()

    assert raised, "Expected BadParameters to be raised for non-string order type"
