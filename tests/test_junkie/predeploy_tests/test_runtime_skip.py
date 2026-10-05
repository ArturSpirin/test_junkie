from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test
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


@Suite()
class RuntimeSkipTestSuite:

    @test()
    def skip_raises_skip_test(self):
        raised = False
        try:
            skip()
        except SkipTest:
            raised = True
        assert raised

    @test()
    def skip_with_reason_stores_reason(self):
        try:
            skip("account not configured")
        except SkipTest as e:
            assert e.reason == "account not configured"
            return
        raise AssertionError("SkipTest was not raised")

    @test()
    def skip_no_reason_defaults_to_none(self):
        try:
            skip()
        except SkipTest as e:
            assert e.reason is None
            return
        raise AssertionError("SkipTest was not raised")

    @test()
    def records_skip_status(self):
        aggregator = Runner([RuntimeSkipSuite]).run()
        assert aggregator.get_basic_report()["tests"][TestCategory.SKIP] >= 1

    @test()
    def does_not_count_as_failure(self):
        aggregator = Runner([RuntimeSkipSuite]).run()
        report = aggregator.get_basic_report()["tests"]
        assert report[TestCategory.FAIL] == 0
        assert report[TestCategory.ERROR] == 0

    @test()
    def other_tests_still_run(self):
        aggregator = Runner([RuntimeSkipSuite]).run()
        report = aggregator.get_basic_report()["tests"]
        assert report[TestCategory.SUCCESS] == 1
        assert report[TestCategory.SKIP] == 1

    @test()
    def mixed_suite_correct_counts(self):
        aggregator = Runner([RuntimeSkipMixedSuite]).run()
        report = aggregator.get_basic_report()["tests"]
        assert report[TestCategory.SKIP] == 2
        assert report[TestCategory.SUCCESS] == 2
        assert report[TestCategory.FAIL] == 0
        assert report[TestCategory.ERROR] == 0

    @test()
    def does_not_retry(self):
        RuntimeSkipNoRetrySuite.call_count = 0
        Runner([RuntimeSkipNoRetrySuite]).run()
        assert RuntimeSkipNoRetrySuite.call_count == 1

    @test()
    def fires_on_skip_event(self):
        _events.clear()
        Runner([RuntimeSkipEventSuite]).run()
        assert "skip" in _events

    @test()
    def does_not_fire_on_success(self):
        _events.clear()
        Runner([RuntimeSkipEventSuite]).run()
        assert "success" not in _events

    @test()
    def fires_on_complete(self):
        _events.clear()
        Runner([RuntimeSkipEventSuite]).run()
        assert "complete" in _events

    @test()
    def fires_on_in_progress(self):
        _events.clear()
        Runner([RuntimeSkipEventSuite]).run()
        assert "in_progress" in _events

    @test()
    def works_with_test_parameters(self):
        aggregator = Runner([RuntimeSkipWithParamsSuite]).run()
        report = aggregator.get_basic_report()["tests"]
        assert report[TestCategory.SKIP] == 1
        assert report[TestCategory.SUCCESS] == 2
