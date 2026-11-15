from test_junkie.builder import Builder
from test_junkie.console import expected_units
from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test
from test_junkie.errors import BadParameters

from tests.junkie_suites import SkipCombinationSuite as fixture
from tests.junkie_suites.SkipCombinationSuite import SkipCombinationSuite, SuiteSkipPerCombinationSuite

SKIP, SUCCESS = TestCategory.SKIP, TestCategory.SUCCESS


def _statuses(test_object, params):
    return {(sp, p): test_object.get_status(p, sp) for sp in ["pg", "sqlite"] for p in params}


@Suite()
class SkipCombinationTestSuite:

    @test()
    def suite_parameter_only(self):
        _, tests = fixture.run(SkipCombinationSuite)
        assert _statuses(tests["by_suite_parameter"], [None]) == {("pg", None): SUCCESS, ("sqlite", None): SKIP}

    @test()
    def parameter_only(self):
        _, tests = fixture.run(SkipCombinationSuite)
        assert _statuses(tests["by_parameter"], [1, 2]) == \
            {("pg", 1): SUCCESS, ("pg", 2): SKIP, ("sqlite", 1): SUCCESS, ("sqlite", 2): SKIP}

    @test()
    def both_skip_one_combination_asked_once_each(self):
        _, tests = fixture.run(SkipCombinationSuite)
        assert _statuses(tests["by_both"], [1, 2]) == \
            {("pg", 1): SUCCESS, ("pg", 2): SUCCESS, ("sqlite", 1): SUCCESS, ("sqlite", 2): SKIP}
        assert [c for c in fixture.CALLS if c[0] == "callable"] == \
            [("callable", "pg", 1), ("callable", "pg", 2), ("callable", "sqlite", 1), ("callable", "sqlite", 2)]
        assert ("by_both", "sqlite", 2) not in fixture.CALLS

    @test()
    def meta_and_suite_parameter(self):
        _, tests = fixture.run(SkipCombinationSuite)
        assert _statuses(tests["by_meta_and_suite_parameter"], [None]) == \
            {("pg", None): SKIP, ("sqlite", None): SUCCESS}

    @test()
    def bound_method(self):
        _, tests = fixture.run(SkipCombinationSuite)
        assert _statuses(tests["by_method"], [None]) == {("pg", None): SKIP, ("sqlite", None): SUCCESS}

    @test()
    def meta_only_and_no_arg_callables_unchanged(self):
        _, tests = fixture.run(SkipCombinationSuite)
        assert tests["by_meta_only"].get_status(None, None) == SKIP
        assert ("by_meta_only", None, None) not in fixture.CALLS
        assert _statuses(tests["by_no_args"], [None]) == {("pg", None): SUCCESS, ("sqlite", None): SUCCESS}

    @test()
    def not_per_suite_parameter_asked_under_first_and_never_dispatched_later(self):
        _, tests = fixture.run(SkipCombinationSuite)
        assert tests["once"].get_status(1, None) == SUCCESS
        assert tests["once"].get_status(2, None) == SKIP
        assert [c for c in fixture.CALLS if c[0] == "once"] == [("once", "pg", 1), ("once", "pg", 2)]
        assert [c for c in fixture.CALLS if c[0] == "once_body"] == [("once_body", None, 1)]

    @test()
    def skipped_combination_not_retried(self):
        _, tests = fixture.run(SkipCombinationSuite)
        test_object = tests["skipped_and_flaky"]
        assert _statuses(test_object, [1, 2]) == \
            {("pg", 1): SUCCESS, ("pg", 2): SKIP, ("sqlite", 1): SUCCESS, ("sqlite", 2): SKIP}
        bodies = [c for c in fixture.CALLS if c[0] == "skipped_and_flaky"]
        assert sorted(bodies) == [("skipped_and_flaky", "pg", 1)] * 2 + [("skipped_and_flaky", "sqlite", 1)] * 2
        assert test_object.is_qualified_for_retry(2, class_param="pg") is False
        assert test_object.is_qualified_for_retry(2, class_param="sqlite") is False

    @test()
    def on_skip_gets_the_combination(self):
        fixture.run(SkipCombinationSuite)
        for unit in [("by_suite_parameter", "sqlite", None), ("by_parameter", "pg", 2), ("by_parameter", "sqlite", 2),
                     ("by_both", "sqlite", 2), ("by_meta_and_suite_parameter", "pg", None),
                     ("by_method", "pg", None), ("once", None, 2), ("skipped_and_flaky", "pg", 2),
                     ("skipped_and_flaky", "sqlite", 2)]:
            assert fixture.SKIPPED.count(unit) == 1, unit

    @test()
    def totals_and_expected_units(self):
        aggregator, _ = fixture.run(SkipCombinationSuite)
        report = aggregator.get_basic_report()["tests"]
        assert (report["total"], report[SUCCESS], report[SKIP]) == (23, 13, 10)
        assert report[TestCategory.FAIL] == 0 and report[TestCategory.ERROR] == 0
        assert expected_units(Builder.get_execution_roster().get(SkipCombinationSuite)) == report["total"]

    @test()
    def suite_skip_declaring_suite_parameter_raises(self):
        try:
            fixture.run(SuiteSkipPerCombinationSuite)
        except BadParameters as error:
            assert "Declare it on the test's skip=" in str(error)
        else:
            raise AssertionError("BadParameters was not raised")
        assert ("never_runs",) not in fixture.CALLS
