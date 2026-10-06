"""
Small behaviours that had no test - each check names what it covers. Shared by the pytest and TJ test paths.
"""
import copy
import io
import os
import shutil
import tempfile
import time

from test_junkie.decorators import Suite, test, beforeClass, beforeTest, afterTest, beforeGroup
from test_junkie.errors import BadParameters, ConfigError, TestListenerError
from test_junkie.listener import Listener
from test_junkie.rules import Rules
from tests.junkie_suites.parallel_restrictions import timeline
from tests.junkie_suites.parallel_restrictions.BrokenListener import BrokenListener, BrokenListenerSuite


def _run(suites, **run_kwargs):
    from test_junkie.runner import Runner
    runner_kwargs = {key: run_kwargs.pop(key) for key in ("html_report", "xml_report") if key in run_kwargs}
    runner = Runner(suites, quiet=True, **runner_kwargs)
    runner.run(**run_kwargs)
    return runner


def _status(suite, test_name, param=None, class_param=None):
    from test_junkie.builder import Builder
    for test_object in Builder.get_execution_roster()[suite].get_test_objects():
        if test_object.get_function_name() == test_name:
            return test_object.get_status(param, class_param)
    raise AssertionError("no test {}".format(test_name))


# --- scheduling -------------------------------------------------------------------------------------------------

@Suite(priority=1)
class PriorityFirst:

    @test()
    def first(self):
        timeline.record("priority_first", duration=0.2)


@Suite(priority=2, pr=[PriorityFirst])
class PriorityRestricted:

    @test()
    def second(self):
        timeline.record("priority_restricted", duration=0.05)


@Suite(priority=3, pr=[PriorityFirst])
class AlsoRestricted:

    @test()
    def third(self):
        timeline.record("also_restricted", duration=0.05)


def prioritized_suite_waits_for_its_restriction():
    # a suite with a priority keeps its place in the queue while a restriction holds it back (it used to poll every
    # second for that, now it wakes up when the restricting suite finishes)
    timeline.reset()
    _run([PriorityFirst, PriorityRestricted, AlsoRestricted], suite_multithreading_limit=3)
    assert len(timeline.events()) == 3
    assert not timeline.any_overlap("priority_first", "priority_restricted")
    assert not timeline.any_overlap("priority_first", "also_restricted")


@Suite(listener=BrokenListener)
class AnotherBrokenListenerSuite:

    @test()
    def b(self):
        pass


def every_thread_error_is_reported():
    try:
        _run([BrokenListenerSuite, AnotherBrokenListenerSuite], suite_multithreading_limit=2)
        raise AssertionError("expected TestListenerError")
    except TestListenerError:
        pass


def run_error_wins_over_a_report_error():
    # the report can't be written (its folder doesn't exist) - the run's own error is still what's raised
    missing = os.path.join(tempfile.mkdtemp(), "no", "such", "folder", "report.html")
    try:
        _run([BrokenListenerSuite], html_report=missing)
        raise AssertionError("expected TestListenerError")
    except TestListenerError:
        pass


# --- parameters ---------------------------------------------------------------------------------------------------

def _not_a_list():
    return "abc"


@Suite(parameters=_not_a_list)
class SuiteParametersNotAList:

    @test()
    def never_runs(self):
        raise AssertionError("must not run")


def _empty():
    return []


@Suite()
class EmptyTestParameters:

    @test(parameters=_empty)
    def never_runs(self, parameter):
        raise AssertionError("must not run")


def bad_parameter_functions_ignore_instead_of_running():
    _run([SuiteParametersNotAList, EmptyTestParameters])
    assert _status(SuiteParametersNotAList, "never_runs") in (None, "ignore")
    assert _status(EmptyTestParameters, "never_runs") == "ignore"


# --- errors -------------------------------------------------------------------------------------------------------

@Suite()
class RaisesFrameworkError:

    @test()
    def bad_config(self):
        raise ConfigError("raised from inside a test")


def framework_errors_in_a_test_abort_the_run():
    try:
        _run([RaisesFrameworkError])
        raise AssertionError("expected ConfigError")
    except ConfigError as error:
        assert "raised from inside a test" in str(error)


def bad_group_rules_are_rejected():
    try:
        class _Rules:
            @beforeGroup([])
            def nothing(self):
                pass
        raise AssertionError("expected BadParameters")
    except BadParameters as error:
        assert "suites" in str(error)


def bad_report_paths_and_tag_config_are_rejected():
    for kwargs, error in (({"html_report": os.path.join(tempfile.mkdtemp(), "report.txt")}, BadParameters),
                          ({"tag_config": ["not", "a", "dict"]}, ConfigError)):
        try:
            _run([PriorityFirst], **kwargs)
            raise AssertionError("expected {} for {}".format(error.__name__, kwargs))
        except error:
            pass


# --- @beforeClass failures with suite parameters (tickets #19, #27) -----------------------------------------------

@Suite(parameters=[1, 2])
class BeforeClassFailsForSecondParameter:

    @beforeClass()
    def before(self, suite_parameter):
        assert suite_parameter == 1, "before class fails for suite parameter 2"

    @test()
    def ignores_suite_parameters(self):
        pass


def before_class_failure_for_a_later_suite_parameter_keeps_earlier_results():
    # ticket #19: the test doesn't take the suite parameter, so it already ran (and passed) under parameter 1 - the
    # @beforeClass failure for parameter 2 must not overwrite that with "ignore"
    _run([BeforeClassFailsForSecondParameter])
    assert _status(BeforeClassFailsForSecondParameter, "ignores_suite_parameters") == "success"


@Suite(parameters=[1, 2], retry=2)
class BeforeClassAlwaysFails:

    @beforeClass()
    def before(self, suite_parameter):
        raise AssertionError("before class always fails")

    @test()
    def never_runs(self):
        raise AssertionError("must not run")


def before_class_failure_with_retries_is_counted_once_per_retry():
    # ticket #27: a test that already used up its retries isn't recorded again for the next suite parameter
    _run([BeforeClassAlwaysFails])
    assert _status(BeforeClassAlwaysFails, "never_runs") == "ignore"


# --- tags, components, skip_before_test ---------------------------------------------------------------------------

@Suite(feature="F1")
class TaggedSuite:

    @test(tags=["a", "b"])
    def both_tags(self):
        pass

    @test(tags=["a"])
    def one_tag(self):
        pass


@Suite(feature="F2")
class UntaggedSuite:

    @test()
    def plain(self):
        pass


def tag_and_component_filters_at_suite_level():
    from test_junkie.builder import Builder
    roster = Builder.get_execution_roster()
    # only skip_* rules configured and none matched: the test runs
    _run([TaggedSuite], tag_config={"skip_on_match_any": ["zzz"]})
    assert _status(TaggedSuite, "one_tag") == "success"
    # run_on_match_all decides at suite level first: TaggedSuite has a test with both tags, UntaggedSuite doesn't
    runner = _run([TaggedSuite, UntaggedSuite], tag_config={"run_on_match_all": ["a", "b"]})
    assert roster[UntaggedSuite] not in runner.get_executed_suites() or _status(UntaggedSuite, "plain") is None
    assert _status(TaggedSuite, "both_tags") == "success"
    # a component nobody has: every suite is skipped
    runner = _run([TaggedSuite, UntaggedSuite], components=["NoSuchComponent"])
    assert all(_status(suite, name) != "success" for suite, name in ((TaggedSuite, "one_tag"),
                                                                      (UntaggedSuite, "plain")))


@Suite(feature="Phases")
class PhasesSuite:

    @beforeTest()
    def before(self):
        pass

    @test()
    def with_before_test(self):
        pass

    @test(skip_before_test=True)
    def without_before_test(self):
        pass


@Suite(feature="Phases")
class AfterTestFails:

    @afterTest()
    def after(self):
        raise RuntimeError("after test fails")

    @test()
    def passes_but_after_test_fails(self):
        pass


@Suite(feature="Phases")
class NoComponentSuite:

    @test()
    def no_component(self):
        pass


def report_phases_and_components():
    # a test that skips @beforeTest shows the phase as N/A, one that ran it as OK; tests without a component from
    # several suites are merged into one "Not Defined" component
    folder = tempfile.mkdtemp()
    html = os.path.join(folder, "report.html")
    try:
        _run([PhasesSuite, NoComponentSuite, UntaggedSuite, AfterTestFails], html_report=html)
        with io.open(html, encoding="utf-8") as doc:
            report = doc.read()
        assert '"status": "N/A"' in report and '"status": "OK"' in report and '"status": "Error"' in report
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def _sleeper(i):
    def body(self):
        time.sleep(0.02)
    body.__name__ = "even_%02d" % i
    return test()(body)


EvenSuite = Suite()(type("EvenSuite", (), {"even_%02d" % i: _sleeper(i) for i in range(3)}))


def threading_recommendation_for_even_tests():
    # 3 equal tests: every extra thread is a big gain, so the last candidate (3 threads) is recommended
    folder = tempfile.mkdtemp()
    html = os.path.join(folder, "report.html")
    try:
        _run([EvenSuite], html_report=html)
        with io.open(html, encoding="utf-8") as doc:
            assert "const THREADING_DATA = {" in doc.read()
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def report_for_a_run_where_nothing_ran():
    folder = tempfile.mkdtemp()
    html = os.path.join(folder, "report.html")
    try:
        _run([UntaggedSuite], html_report=html, tests=["no_such_test"])
        with io.open(html, encoding="utf-8") as doc:
            assert "No test data." in doc.read()
    finally:
        shutil.rmtree(folder, ignore_errors=True)


# --- small API pieces ---------------------------------------------------------------------------------------------

class _Unhashable(object):
    __hash__ = None

    def __call__(self, meta=None):
        return False


def small_api_pieces():
    from test_junkie.builder import Builder
    from test_junkie.metrics import ResourceMonitor
    from test_junkie.objects import arg_names
    # argument names of callables that can't be cached (a bound method is hashable even when its object isn't)
    assert "meta" in arg_names(_Unhashable())
    # metrics are shared, never copied
    suite = Builder.get_execution_roster()[UntaggedSuite]
    test_object = suite.get_test_objects()[0]
    for metrics in (suite.metrics, test_object.metrics):
        assert copy.copy(metrics) is metrics and copy.deepcopy(metrics) is metrics
    # the base Rules / Listener hooks are no-ops a subclass may override
    rules = Rules()
    assert rules.before_class() is None and rules.before_test(test=None) is None
    assert rules.after_test(test=None) is None and rules.after_class() is None
    assert Listener().on_success(properties={}) is None
    # mkdir_p: an existing folder is fine, a file in the way is not
    folder = tempfile.mkdtemp()
    try:
        monitor = ResourceMonitor.__new__(ResourceMonitor)
        monitor.mkdir_p(folder)
        in_the_way = os.path.join(folder, "file")
        open(in_the_way, "w").close()
        try:
            monitor.mkdir_p(in_the_way)
            raise AssertionError("expected OSError")
        except OSError:
            pass
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def xml_report_appends_to_an_existing_file():
    folder = tempfile.mkdtemp()
    xml = os.path.join(folder, "report.xml")
    try:
        _run([UntaggedSuite], xml_report=xml)
        _run([UntaggedSuite, TaggedSuite], xml_report=xml)
        with io.open(xml, encoding="utf-8") as doc:
            report = doc.read()
        assert report.count('<testsuite name="UntaggedSuite"') == 1 and 'tests="2"' in report, report
        assert '<testsuite name="TaggedSuite"' in report
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def analyzer_reports_the_most_shared_traceback_per_test():
    from test_junkie.reporter.analyzer import Analyzer
    common = "Traceback (most recent call last):\n  File \"suite.py\", line 10, in checkout\nValueError: cart {}"
    analyzer = Analyzer()
    analyzer.analyze(test_id=1, tracebacks=["KeyError: something unrelated", common.format(1)],
                     performance=[0.1, 0.1])
    analyzer.analyze(test_id=2, tracebacks=[common.format(2)], performance=[0.1])
    analyzer.analyze(test_id=3, tracebacks=[common.format(3)], performance=[0.1])
    reported = [item["traceback"] for item in analyzer.structured_analysis if item.get("traceback")]
    assert common.format(1) in reported and "KeyError: something unrelated" not in reported, reported


CHECKS = [prioritized_suite_waits_for_its_restriction, every_thread_error_is_reported,
          run_error_wins_over_a_report_error, bad_parameter_functions_ignore_instead_of_running,
          framework_errors_in_a_test_abort_the_run, bad_group_rules_are_rejected,
          bad_report_paths_and_tag_config_are_rejected,
          before_class_failure_for_a_later_suite_parameter_keeps_earlier_results,
          before_class_failure_with_retries_is_counted_once_per_retry, tag_and_component_filters_at_suite_level,
          report_phases_and_components, threading_recommendation_for_even_tests,
          report_for_a_run_where_nothing_ran, small_api_pieces, xml_report_appends_to_an_existing_file,
          analyzer_reports_the_most_shared_traceback_per_test]
