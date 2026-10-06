"""
Core behavior checks that close the remaining coverage gaps in runner.py / objects.py / html_reporter.py.
Shared by the pytest and TJ test paths.
"""
import threading
import time

from test_junkie.decorators import Suite, test
from test_junkie.errors import ConfigError

_LOCK = threading.Lock()
INTERVALS = {}
ATTEMPTS = []


@Suite(parameters=[])
class EmptySuiteParameters:

    @test()
    def never_runs(self, suite_parameter):
        pass


def _not_a_list():
    return "not a list"


@Suite()
class BadTestParameters:

    @test(parameters=_not_a_list)
    def bad_provider(self, parameter):
        pass


@Suite()
class Tagged:

    @test(tags=["smoke"])
    def tagged(self):
        pass


def _record(name):
    start = time.time()
    time.sleep(0.15)
    with _LOCK:
        INTERVALS[name] = (start, time.time())


@Suite()
class MixedParallelism:

    @test(priority=1)
    def parallel_a(self):
        _record("parallel_a")

    @test(priority=2)
    def parallel_b(self):
        _record("parallel_b")

    @test(priority=3, parallelized=False)
    def alone(self):
        _record("alone")


@Suite()
class RetryFilters:

    @test(retry=3, retry_on=[ConnectionError])
    def value_error_is_not_retried(self):
        ATTEMPTS.append("value_error")
        raise ValueError("not in retry_on")

    @test(retry=3, retry_on=[ConnectionError])
    def connection_error_is_retried(self):
        ATTEMPTS.append("connection_error")
        raise ConnectionError("flaky network")


def _run(suites, **kwargs):
    from test_junkie.runner import Runner
    runner = Runner(suites, quiet=True)
    runner.run(**kwargs)
    return runner


def reporter_static_helpers():
    from test_junkie.reporter.html_reporter import Reporter
    assert Reporter.round([1, 2]) == "1.5" and Reporter.round([]) == "0"
    assert Reporter.total_up([1.25, 1]) == "2.25" and Reporter.total_up([]) == "0"
    assert Reporter.escape("<a href='x'>") == "&lt;a href=&#x27;x&#x27;&gt;"


def bad_parameter_providers_ignore_their_tests():
    from test_junkie.constants import TestCategory, SuiteCategory
    runner = _run([EmptySuiteParameters, BadTestParameters])
    by_name = {suite.get_class_name(): suite for suite in runner.get_executed_suites()}
    assert by_name["EmptySuiteParameters"].get_status() == SuiteCategory.IGNORE
    bad_test = by_name["BadTestParameters"].get_test_objects()[0]
    assert bad_test.metrics.get_metrics()["None"]["None"]["status"] == TestCategory.IGNORE


def malformed_tag_config_raises_config_error():
    try:
        _run([Tagged], tag_config={"run_on_match_any": 5})
        raise AssertionError("Expected ConfigError for a malformed tag_config")
    except ConfigError:
        pass


def non_parallel_test_never_overlaps_others():
    INTERVALS.clear()
    _run([MixedParallelism], test_multithreading_limit=3)
    alone_start, alone_end = INTERVALS["alone"]
    for name in ("parallel_a", "parallel_b"):
        start, end = INTERVALS[name]
        assert end <= alone_start or start >= alone_end, "{} overlapped the parallelized=False test".format(name)


def retry_on_only_retries_listed_exceptions():
    del ATTEMPTS[:]
    _run([RetryFilters])
    assert ATTEMPTS.count("value_error") == 1
    assert ATTEMPTS.count("connection_error") == 3


def object_repr_and_getters():
    runner = _run([Tagged])
    suite = runner.get_executed_suites()[0]
    test_object = suite.get_test_objects()[0]
    assert repr(test_object) == "<Tagged.tagged>"
    assert suite.get_test_count() == 1
    assert test_object.get_function_module() == __name__
    assert test_object.get_suite_id() == suite.get_suite_id()


CHECKS = [reporter_static_helpers, bad_parameter_providers_ignore_their_tests,
          malformed_tag_config_raises_config_error, non_parallel_test_never_overlaps_others,
          retry_on_only_retries_listed_exceptions, object_repr_and_getters]
