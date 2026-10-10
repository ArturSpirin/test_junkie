"""
Core-module behaviours that had no test (views, conflicts, builder, meta, metrics, objects, retry, reporters) - each
check names what it covers. Shared by the pytest and TJ test paths.
"""
import contextlib
import io
import json
import os
import shutil
import tempfile
from xml.etree.ElementTree import parse

from test_junkie.decorators import Suite, test, beforeTest, afterTest
from test_junkie.errors import BadParameters, TestJunkieUsageError
from test_junkie.meta import Meta
from test_junkie.objects import Limiter
from test_junkie.retry import RetryPolicy, When


def _run(suites, **run_kwargs):
    from test_junkie.runner import Runner
    runner_kwargs = {key: run_kwargs.pop(key) for key in ("html_report", "xml_report", "json_report")
                     if key in run_kwargs}
    runner = Runner(suites, quiet=True, **runner_kwargs)
    runner.run(**run_kwargs)
    return runner


def _test_object(suite, test_name):
    from test_junkie.builder import Builder
    for test_object in Builder.get_execution_roster()[suite].get_test_objects():
        if test_object.get_function_name() == test_name:
            return test_object
    raise AssertionError("no test {}".format(test_name))


# --- views: the read-only window hooks and Rules get ---------------------------------------------------------------

@Suite()
class ViewedSuite:

    @test(parameters=[1, 2], tags=["view"])
    def viewed(self, parameter):
        pass


class _CopyKeepsFailing(object):
    """deepcopy raises RuntimeError every time, like a dict changing size in another thread"""

    def __deepcopy__(self, memo):
        raise RuntimeError("dictionary changed size during iteration")


def view_copy_falls_back_to_a_shallow_copy():
    from test_junkie import views
    value = _CopyKeepsFailing()
    copied = views._copy([value])  # three deepcopy attempts fail, then a shallow copy of the list
    assert copied == [value] and copied is not None


def read_only_test_view_keeps_local_changes():
    from test_junkie.objects import TestObject
    from test_junkie.views import TestView, SuiteView
    _run([ViewedSuite])
    live = _test_object(ViewedSuite, "viewed")
    view = TestView(live)
    assert isinstance(view, TestObject)
    assert repr(view).startswith("<TestView of ")
    # private names aren't forwarded
    try:
        view._secret
    except AttributeError:
        pass
    else:
        raise AssertionError("a private attribute was reachable through the view")
    # assignments stay on the view; deleting one brings the live value back
    view.note = "mine"
    assert view.note == "mine" and not hasattr(live, "note")
    del view.note
    try:
        view.note
    except AttributeError:
        pass
    else:
        raise AssertionError("a deleted local attribute was still there")
    # never runs a parameters function, returns the declared list as a copy
    params = view.get_parameters(process_functions=True)
    assert params == [1, 2]
    params.append(3)
    assert live.get_parameters() == [1, 2]
    assert view.get_function_object() is live.get_function_object()
    # the suite is wrapped too, and its class/instance are the user's own objects
    suite_view = view.suite
    assert isinstance(suite_view, SuiteView)
    assert suite_view.get_class_object() is ViewedSuite
    assert suite_view.get_class_instance() is live.suite.get_class_instance()


# --- conflicts_with targets ------------------------------------------------------------------------------------------

def _conflict_error(make):
    try:
        make()
    except BadParameters as error:
        return str(error)
    raise AssertionError("no BadParameters")


def pr_and_conflicts_with_together_are_rejected():
    def make():
        @Suite(pr=[ViewedSuite], conflicts_with=[ViewedSuite])
        class Both:
            @test()
            def t(self):
                pass
    assert "got both pr= and conflicts_with=" in _conflict_error(make)


def _run_error(suite):
    from test_junkie.runner import Runner
    try:
        Runner([suite]).run(quiet=True)
    except BadParameters as error:
        return str(error)
    raise AssertionError("{} wasn't rejected".format(suite.__name__))


def conflicts_with_a_name_two_suites_share_is_rejected():
    def make():
        @Suite()
        class CoreCovTwin:
            @test()
            def t(self):
                pass
        return CoreCovTwin
    make()
    make()

    @Suite()
    class CoreCovTwinUser:
        @test(conflicts_with=["CoreCovTwin.t"])
        def t(self):
            pass
    assert "more than one suite is called 'CoreCovTwin'" in _run_error(CoreCovTwinUser)


def conflicts_with_an_unknown_test_of_a_known_suite_is_rejected():
    @Suite()
    class CoreCovTarget:
        @test()
        def known(self):
            pass

    @Suite()
    class CoreCovMissingTest:
        @test(conflicts_with=["CoreCovTarget.nope"])
        def t(self):
            pass
    assert "CoreCovTarget.nope" in _run_error(CoreCovMissingTest)


def suite_conflicting_with_itself_by_name_is_rejected():
    @Suite(conflicts_with=["CoreCovItself"])
    class CoreCovItself:
        @test()
        def t(self):
            pass
    assert "names itself" in _run_error(CoreCovItself)


# --- meta --------------------------------------------------------------------------------------------------------

class _Unprintable(object):
    def __str__(self):
        raise ValueError("no text")

    def __repr__(self):
        return "<unprintable>"


def report_value_falls_back_to_repr():
    from test_junkie.meta import report_value
    assert report_value(_Unprintable()) == "<unprintable>"
    assert report_value({"k": [_Unprintable()]}) == {"k": ["<unprintable>"]}


def _outside_any_test(function):
    """Runs function on a new thread: no run context there, even when these checks run inside a TJ test"""
    import threading
    outcome = {}

    def target():
        try:
            outcome["value"] = function()
        except BaseException as error:
            outcome["error"] = error
    thread = threading.Thread(target=target)
    thread.start()
    thread.join()
    if "error" in outcome:
        raise outcome["error"]
    return outcome.get("value")


def suite_meta_outside_a_run_is_a_usage_error():
    def update():
        try:
            Meta.suite.update(build="1")
        except TestJunkieUsageError as error:
            return str(error)
        raise AssertionError("Meta.suite.update() outside a run was accepted")
    assert "needs a running suite" in _outside_any_test(update)


def old_style_get_meta_outside_a_test_returns_none():
    _run([ViewedSuite])
    assert _outside_any_test(lambda: Meta.get_meta(suite=ViewedSuite())) is None


def meta_append_onto_a_tuple():
    seen = {}

    @Suite()
    class CoreCovAppend:
        @test()
        def appends(self):
            Meta.update(tags=("a",))  # a tuple, set earlier in this same attempt
            Meta.append("tags", "b")
            seen["all"] = Meta.get_meta()

    _run([CoreCovAppend])
    live = _test_object(CoreCovAppend, "appends")
    assert seen["all"]["tags"] == ["a", "b"], seen
    assert live.get_meta()["tags"] == ["a", "b"]
    assert live.get_meta_attempts() == [{"attempt": 1, "meta_set": {"tags": ["a", "b"]}}], live.get_meta_attempts()


# --- metrics, debugger -------------------------------------------------------------------------------------------

def aggregator_percentage_and_console_summary():
    from test_junkie.builder import Builder
    from test_junkie.metrics import Aggregator
    assert Aggregator.percentage(8, 2) == "25.00"
    assert Aggregator.percentage(8, 0) == "0"
    _run([ViewedSuite])
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        Aggregator.present_console_output(Aggregator([Builder.get_execution_roster()[ViewedSuite]]))
    assert "ViewedSuite" in printed.getvalue() and "[PASSED]" in printed.getvalue(), printed.getvalue()


def resource_monitor_cleanup_warns_when_the_file_is_gone():
    from test_junkie.metrics import ResourceMonitor
    monitor = ResourceMonitor()  # never started, so its temp file was never written
    warned = io.StringIO()
    with contextlib.redirect_stderr(warned):
        monitor.cleanup()
    assert "Failed to remove resource monitoring temp file" in warned.getvalue(), warned.getvalue()


def suppressed_stdout_off_leaves_output_alone():
    from test_junkie.debugger import suppressed_stdout
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        with suppressed_stdout(suppress=False):
            print("still shown")
    assert printed.getvalue() == "still shown\n"


# --- objects: skip, Limiter --------------------------------------------------------------------------------------

def skip_given_a_type_fails_at_run_time():
    # the decorator accepts a subclass of bool, so skip=bool (the type, not a value) gets past it
    @Suite()
    class CoreCovSkipType:
        @test(skip=bool)
        def t(self):
            pass
    assert "not a supported type" in _run_error(CoreCovSkipType)


class _Final(Exception):
    def __init_subclass__(cls, **kwargs):  # can't be subclassed, so a truncated copy can't be made
        raise TypeError("final")


class _NoText(Exception):
    def __str__(self):
        raise ValueError("no text")


def exception_messages_that_cannot_be_truncated_are_kept():
    no_text = _NoText()
    assert Limiter.parse_exception_object(no_text) is no_text
    long_error = _Final("x" * (Limiter.EXCEPTION_MESSAGE_LIMIT + 100))
    assert Limiter.parse_exception_object(long_error) is long_error


def limits_off_means_no_test_throttling():
    Limiter.ACTIVE = False
    try:
        assert Limiter.get_test_throttling() == 0
    finally:
        Limiter.ACTIVE = True


def wait_turn_stops_on_cancel():
    gate = ("core-coverage", "wait_turn")
    assert Limiter.wait_turn(gate, 30) is True  # the first start doesn't wait
    assert Limiter.wait_turn(gate, 30, cancelled=lambda: True) is False


def pools_listed_acquired_and_released():
    name = "core-coverage-pool"
    Limiter.pool(name, max_concurrent=2, min_interval=30)
    try:
        assert Limiter.get_pools()[name] == {"max_concurrent": 2, "min_interval": 30, "in_use": 0}
        assert Limiter.acquire(["core-coverage-no-such-pool"]) == []  # e.g. removed after the run was checked
        first = Limiter.acquire([name])
        assert Limiter.get_pools()[name]["in_use"] == 1
        # the next start waits min_interval: a cancel during that wait gives the slot back
        assert Limiter.acquire([name], cancelled=lambda: True) is None
        assert Limiter.get_pools()[name]["in_use"] == 1
        Limiter.release(first)
        assert Limiter.get_pools()[name]["in_use"] == 0
    finally:
        Limiter.remove_pools(name)


def uses_with_a_non_name_is_rejected():
    @Suite()
    class CoreCovUsesNumber:
        @test(uses=[5])
        def t(self):
            pass
    assert "takes pool names, got 5" in _run_error(CoreCovUsesNumber)


def unknown_limit_is_rejected():
    try:
        Limiter.validate({"core_coverage_limit": 1})
    except BadParameters as error:
        assert 'Unknown limit "core_coverage_limit"' in str(error)
    else:
        raise AssertionError("an unknown limit was accepted")


# --- retry -------------------------------------------------------------------------------------------------------

class _TimeoutsOnly(RetryPolicy):
    retry_on = [TimeoutError]
    attempts = 1


@Suite(retry=2)
class SuiteRetryWithPolicy:

    @test(retry=_TimeoutsOnly)
    def times_out(self):
        raise TimeoutError("slow")

    @test(retry=_TimeoutsOnly)
    def breaks(self):
        raise ValueError("broken")


def suite_retry_pass_asks_the_test_policy():
    _run([SuiteRetryWithPolicy])
    runs = {name: len(_test_object(SuiteRetryWithPolicy, name).metrics.get_metrics()["None"]["None"]["statuses"])
            for name in ("times_out", "breaks")}
    assert runs == {"times_out": 2, "breaks": 1}, runs


def when_and_decision_details():
    try:
        When(TimeoutError, attempts=2, name=5)
    except BadParameters as error:
        assert "When.name must be text" in str(error)
    else:
        raise AssertionError("When(name=5) was accepted")
    assert When(TimeoutError, attempts=2, name="slow calls").label() == "slow calls"
    decision = _TimeoutsOnly().decide([])
    assert not decision and decision.reason == "no error"
    assert repr(decision) == "<Decision retry=False when=None delay=0.0 run=0/0>", repr(decision)


class _Jittery(RetryPolicy):
    attempts = 3
    delay = 1
    jitter = 0.5


def jitter_adds_a_bounded_random_wait():
    policy = _Jittery()
    decision = policy.decide([ValueError("x")])
    assert decision and 1 <= decision.delay <= 1.5, decision
    assert all(1 <= policy.wait(decision.when, 1) <= 1.5 for _ in range(20))


def retry_policy_option_must_name_a_policy():
    from test_junkie.retry import load
    try:
        load("os:sep")
    except BadParameters as error:
        assert "--retry-policy takes a RetryPolicy subclass or instance" in str(error), str(error)
    else:
        raise AssertionError("--retry-policy os:sep was accepted")


# --- reporters ---------------------------------------------------------------------------------------------------

@Suite()
class ReportEdgeSuite:

    @afterTest()
    def after(self):
        pass

    @test(skip=True)
    def skipped(self):
        pass

    @test()
    def attached(self):
        Meta.attach("note.txt", b"hello")
        os.remove(Meta.get("attachments")[-1]["path"])  # gone before the report is written


@Suite()
class BrokenBeforeTestSuite:

    @beforeTest()
    def before(self):
        raise RuntimeError("setup broke")

    @afterTest()
    def after(self):
        pass

    @test()
    def t(self):
        pass


def reports_cover_skips_broken_hooks_and_lost_attachments():
    folder = tempfile.mkdtemp(prefix="tj_core_reports_")
    try:
        html, xml = os.path.join(folder, "r.html"), os.path.join(folder, "r.xml")
        _run([ReportEdgeSuite, BrokenBeforeTestSuite], html_report=html, xml_report=xml)
        with open(html, encoding="utf-8") as page:
            assert "data:text/plain" not in page.read()  # the removed attachment is left out
        cases = {case.get("name"): case for case in parse(xml).getroot().iter("testcase")}
        skipped = cases["skipped"].find("failure")
        assert skipped is not None and skipped.get("type") == "failure", cases
    finally:
        shutil.rmtree(folder, ignore_errors=True)


@Suite()
class InterruptedAfterTestSuite:

    @beforeTest()
    def before(self):  # records a row for the test before its status is known
        pass

    @afterTest()
    def after(self):
        raise KeyboardInterrupt()

    @test()
    def t(self):
        pass


def reports_after_an_interrupt_in_after_test():
    # no html_report here: with one, the run currently ends in a StatisticsError instead (reported as a bug)
    from test_junkie.runner import Runner
    folder = tempfile.mkdtemp(prefix="tj_core_interrupt_")
    try:
        paths = {kind: os.path.join(folder, "r." + kind) for kind in ("xml", "json")}
        runner = Runner([InterruptedAfterTestSuite], quiet=True, xml_report=paths["xml"])
        try:
            runner.run(json_report=paths["json"])
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError("the KeyboardInterrupt was swallowed")
        with open(paths["json"], encoding="utf-8") as doc:
            assert [suite["name"] for suite in json.load(doc)["suites"]] == ["InterruptedAfterTestSuite"]
        parse(paths["xml"])
    finally:
        shutil.rmtree(folder, ignore_errors=True)


CHECKS = [view_copy_falls_back_to_a_shallow_copy, read_only_test_view_keeps_local_changes,
          pr_and_conflicts_with_together_are_rejected, conflicts_with_a_name_two_suites_share_is_rejected,
          conflicts_with_an_unknown_test_of_a_known_suite_is_rejected, suite_conflicting_with_itself_by_name_is_rejected,
          report_value_falls_back_to_repr, suite_meta_outside_a_run_is_a_usage_error,
          old_style_get_meta_outside_a_test_returns_none, meta_append_onto_a_tuple,
          aggregator_percentage_and_console_summary, resource_monitor_cleanup_warns_when_the_file_is_gone,
          suppressed_stdout_off_leaves_output_alone, skip_given_a_type_fails_at_run_time,
          exception_messages_that_cannot_be_truncated_are_kept, limits_off_means_no_test_throttling,
          wait_turn_stops_on_cancel, pools_listed_acquired_and_released, uses_with_a_non_name_is_rejected,
          unknown_limit_is_rejected, suite_retry_pass_asks_the_test_policy, when_and_decision_details,
          jitter_adds_a_bounded_random_wait, retry_policy_option_must_name_a_policy,
          reports_cover_skips_broken_hooks_and_lost_attachments, reports_after_an_interrupt_in_after_test]
