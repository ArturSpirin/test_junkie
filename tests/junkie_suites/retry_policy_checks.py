"""
RetryPolicy checks (0.9a8), shared by both test paths:
tests/pytest/predeploy_tests/retry/test_retry_policy.py and tests/test_junkie/predeploy_tests/test_retry_policy.py
"""
import json
import os
import re
import tempfile
import threading
import time

from test_junkie.builder import Builder
from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test, beforeClass, afterClass
from test_junkie.errors import BadParameters
from test_junkie.listener import Listener
from test_junkie.objects import Limiter
from test_junkie.retry import RetryPolicy, When
from test_junkie.runner import Runner

RETRIES = []  # what on_retry saw
TIMES = {}  # name -> [monotonic start of each run]
COUNTS = {}


def _mark(name):
    TIMES.setdefault(name, []).append(time.monotonic())
    COUNTS[name] = COUNTS.get(name, 0) + 1
    return COUNTS[name]


class Recorder(Listener):

    def on_retry(self, **kwargs):
        RETRIES.append(dict(kwargs["properties"]["retry"], test=kwargs["properties"]["jm"]["jto"].get_function_name()))


class Flaky(RetryPolicy):
    no_retry_on = [PermissionError]
    when = [When(TimeoutError, attempts=3, delay=0.15),
            When(message="503", attempts=2, delay=0.25)]


class Backoff(RetryPolicy):
    attempts = 4
    delay = 0.1
    backoff = 2
    max_delay = 0.25


class Plain(RetryPolicy):
    attempts = 3


class Caused(RetryPolicy):
    attempts = 2
    retry_on = [TimeoutError]
    chain = True


class Pattern(RetryPolicy):
    attempts = 2
    message = re.compile(r"HTTP 5\d\d")


@Suite(listener=Recorder)
class PolicySuite:

    @test(retry=Flaky)
    def timeouts(self):
        _mark("timeouts")
        raise TimeoutError("slow")

    @test(retry=Flaky)
    def recovers_after_503(self):
        if _mark("recovers_after_503") < 2:
            raise RuntimeError("HTTP 503 " + "x" * 6000)  # long enough that the stored copy is truncated

    @test(retry=Flaky)
    def switches_condition(self):
        run = _mark("switches_condition")
        raise (RuntimeError("got 503") if run % 2 else TimeoutError("slow"))

    @test(retry=Flaky)
    def never_on_permission(self):
        _mark("never_on_permission")
        raise PermissionError("no")

    @test(retry=Flaky)
    def unmatched_failure(self):
        _mark("unmatched_failure")
        assert False

    @test(retry=Backoff)
    def backs_off(self):
        _mark("backs_off")
        assert False

    @test(retry=Backoff(attempts=2, delay=0))
    def instance_overrides(self):
        _mark("instance_overrides")
        assert False

    @test(retry=Caused)
    def matches_the_cause(self):
        _mark("matches_the_cause")
        try:
            raise TimeoutError("inner")
        except TimeoutError as error:
            raise RuntimeError("outer") from error

    @test(retry=Pattern)
    def matches_a_pattern(self):
        if _mark("matches_a_pattern") < 2:
            raise RuntimeError("HTTP 502 bad gateway")


@Suite(retry_policy=Plain)
class SuitePolicySuite:

    @test()
    def uses_suite_policy(self):
        _mark("uses_suite_policy")
        assert False

    @test(retry=1)
    def opts_out(self):
        _mark("opts_out")
        assert False

    @test(retry=Flaky)
    def own_policy_wins(self):
        _mark("own_policy_wins")
        raise PermissionError("no")


class Slow(RetryPolicy):
    attempts = 3
    delay = 5


@Suite()
class WaitSuite:

    @test(retry=Slow, uses="retry_policy_slot")
    def waits(self):
        _mark("waits")
        assert False

    @test(uses="retry_policy_slot")
    def neighbour(self):
        _mark("neighbour")


def _reset():
    del RETRIES[:]
    TIMES.clear()
    COUNTS.clear()


def _variant(suite_class, name):
    suite = Builder.get_execution_roster().get(suite_class)
    for test_object in suite.get_test_objects():
        if test_object.get_function_name() == name:
            return test_object, test_object.metrics.get_metrics()["None"]["None"]
    raise AssertionError(name)


_RAN = {}


def _policy_run():
    """PolicySuite runs once; every check reads its results."""
    if "policy" not in _RAN:
        _reset()
        Runner([PolicySuite]).run(quiet=True)
        _RAN["policy"] = (list(RETRIES), dict(TIMES), dict(COUNTS))
    return _RAN["policy"]


def each_condition_has_its_own_budget():
    retries, times, counts = _policy_run()
    assert counts["timeouts"] == 3
    # 503 -> retry, timeout -> retry (its own budget), 503 again -> the 503 budget of 2 is spent -> stop
    assert counts["switches_condition"] == 3
    _, data = _variant(PolicySuite, "switches_condition")
    assert len(data["statuses"]) == counts["switches_condition"]


def no_retry_on_and_unmatched_failures_run_once():
    _, _, counts = _policy_run()
    assert counts["never_on_permission"] == 1
    assert counts["unmatched_failure"] == 1


def delays_are_waited_between_runs():
    _, times, _ = _policy_run()
    gaps = [b - a for a, b in zip(times["timeouts"], times["timeouts"][1:])]
    assert len(gaps) == 2 and all(gap >= 0.14 for gap in gaps), gaps


def backoff_doubles_up_to_max_delay():
    _, times, counts = _policy_run()
    assert counts["backs_off"] == 4
    gaps = [b - a for a, b in zip(times["backs_off"], times["backs_off"][1:])]
    assert 0.09 <= gaps[0] < 0.19 and 0.19 <= gaps[1] < 0.29 and 0.24 <= gaps[2] < 0.34, gaps  # 0.1, 0.2, 0.25 (cap)


def message_matches_the_raised_error_not_the_truncated_copy():
    _, _, counts = _policy_run()
    assert counts["recovers_after_503"] == 2
    test_object, data = _variant(PolicySuite, "recovers_after_503")
    assert data["status"] == TestCategory.SUCCESS


def instance_overrides_class_fields():
    _, _, counts = _policy_run()
    assert counts["instance_overrides"] == 2


def chain_and_regex_match():
    _, _, counts = _policy_run()
    assert counts["matches_the_cause"] == 2
    assert counts["matches_a_pattern"] == 2


def on_retry_and_metrics_record_each_retry():
    retries, _, _ = _policy_run()
    timeouts = [r for r in retries if r["test"] == "timeouts"]
    assert [(r["run"], r["policy"], r["when"]) for r in timeouts] == [(1, "Flaky", "TimeoutError"),
                                                                      (2, "Flaky", "TimeoutError")]
    assert all(r["waited"] == 0.15 for r in timeouts)
    test_object, _ = _variant(PolicySuite, "recovers_after_503")
    assert test_object.metrics.get_retries(None, None) == [{"run": 1, "policy": "Flaky", "when": '"503"',
                                                            "waited": 0.25}]


def suite_policy_applies_unless_the_test_sets_retry():
    _reset()
    Runner([SuitePolicySuite]).run(quiet=True)
    assert COUNTS == {"uses_suite_policy": 3, "opts_out": 1, "own_policy_wins": 1}, COUNTS


def plain_retry_fires_on_retry_without_a_policy():
    _reset()

    @Suite(listener=Recorder)
    class PlainRetrySuite:
        @test(retry=2)
        def plain(self):
            assert False

    Runner([PlainRetrySuite]).run(quiet=True)
    assert [(r["run"], r["policy"], r["when"], r["waited"]) for r in RETRIES] == [(1, None, None, 0)]


def cancel_ends_the_wait_and_pool_slots_are_free_meanwhile():
    _reset()
    Limiter.pool("retry_policy_slot", max_concurrent=1)
    runner = Runner([WaitSuite])
    threading.Timer(1.0, runner.cancel).start()
    started = time.monotonic()
    runner.run(quiet=True, test_multithreading_limit=2)
    assert time.monotonic() - started < 3, "a cancel should end the 5s wait"
    assert COUNTS == {"waits": 1, "neighbour": 1}, COUNTS
    assert TIMES["neighbour"][0] - TIMES["waits"][0] < 0.9, "neighbour should get the slot during the wait"


def no_retry_flag_turns_a_policy_off():
    """tj run --no-retry must switch a policy off too, and --retry N caps it"""
    _reset()

    @Suite()
    class NoRetrySuite:
        @test(retry=Plain)
        def off(self):
            _mark("off")
            assert False

    Runner([NoRetrySuite]).run(quiet=True)
    assert COUNTS["off"] == 3
    _reset()
    Runner([NoRetrySuite]).run(quiet=True, no_retry=True)
    assert COUNTS["off"] == 1, COUNTS
    _reset()
    Runner([NoRetrySuite]).run(quiet=True, retry=2)  # --retry N caps the runs; the policy still decides
    assert COUNTS["off"] == 2, COUNTS


def reports_show_the_retry():
    _reset()
    folder = tempfile.mkdtemp(prefix="tj_retry_policy_")
    path = os.path.join(folder, "report.json")

    @Suite()
    class ReportedSuite:
        @test(retry=Flaky)
        def reported(self):
            if _mark("reported") < 2:
                raise TimeoutError("slow")

    Runner([ReportedSuite]).run(quiet=True, json_report=path, html_report=os.path.join(folder, "report.html"))
    with open(path, encoding="utf-8") as doc:
        runs = json.load(doc)["suites"][0]["tests"][0]["runs"]
    assert runs[0]["retry"] == {"run": 1, "policy": "Flaky", "when": "TimeoutError", "waited": 0.15}
    assert runs[1]["retry"] is None
    with open(os.path.join(folder, "report.html"), encoding="utf-8") as doc:
        assert '"policy": "Flaky"' in doc.read()


def bad_policies_are_rejected_when_defined():
    cases = {"attempts = 0": "attempts", "retry_on = [int]": "retry_on", "delay = -1": "delay",
             "backoff = 0.5": "backoff", "chain = 1": "chain", "when = ['x']": "when", "message = 5": "message",
             "when = [When(TimeoutError)]": "attempts", "retry_on = [TimeoutError]\n    when = [When(attempts=2)]":
             "when"}
    for body, field in cases.items():
        try:
            exec("class Bad(RetryPolicy):\n    " + body, {"RetryPolicy": RetryPolicy, "When": When})
        except BadParameters as error:
            assert field in str(error), (body, str(error))
        else:
            raise AssertionError("no error for: " + body)
    try:
        Plain(atempts=3)
    except BadParameters as error:
        assert "atempts" in str(error)
    else:
        raise AssertionError("unknown field accepted")


def mixing_a_policy_with_retry_on_is_rejected():
    try:
        @Suite()
        class Mixed:
            @test(retry=Plain, retry_on=[TimeoutError])
            def mixed(self):
                pass
    except BadParameters as error:
        assert "retry_on" in str(error)
    else:
        raise AssertionError("policy + retry_on accepted")


# -- phase 2: should_retry / before_retry, max_time, reset="class" ---------------------------------------------------

PHASE2 = []


class Vetoes(RetryPolicy):
    attempts = 3

    def should_retry(self, error, decision, test):
        PHASE2.append(("should_retry", type(error).__name__, decision.retry, test.get_function_name()))
        return decision.retry and "stop" not in str(error)


class Forces(RetryPolicy):
    attempts = 2
    retry_on = [TimeoutError]

    def should_retry(self, error, decision, test):
        return True  # even for errors retry_on doesn't list


class Prepares(RetryPolicy):
    attempts = 3

    def before_retry(self, error, decision, test):
        PHASE2.append(("before_retry", str(error), decision.run, test.get_function_name()))


class BrokenPrepare(RetryPolicy):
    attempts = 3

    def before_retry(self, error, decision, test):
        raise RuntimeError("token service down")


class OutOfTime(RetryPolicy):
    attempts = 10
    delay = 0.2
    max_time = 0.5


class Resets(RetryPolicy):
    attempts = 3
    reset = "class"


class ResetsOn503(RetryPolicy):
    when = [When(message="503", attempts=2, reset="class"), When(TimeoutError, attempts=2)]


@Suite()
class HookSuite:

    @test(retry=Vetoes)
    def vetoed(self):
        _mark("vetoed")
        raise RuntimeError("stop now")

    @test(retry=Forces)
    def forced(self):
        _mark("forced")
        raise ValueError("not in retry_on")

    @test(retry=Prepares)
    def prepared(self):
        if _mark("prepared") < 3:
            raise RuntimeError("expired")

    @test(retry=BrokenPrepare)
    def broken_prepare(self):
        _mark("broken_prepare")
        assert False

    @test(retry=OutOfTime)
    def out_of_time(self):
        _mark("out_of_time")
        assert False


@Suite(parameters=["admin"])
class ResetSuite:

    @beforeClass()
    def set_up(self, suite_parameter):
        PHASE2.append("before_class")

    @afterClass()
    def tear_down(self):
        PHASE2.append("after_class")

    @test(retry=Resets)
    def first(self, suite_parameter):
        PHASE2.append("first")
        if _mark("first") < 2:
            assert False

    @test(retry=Resets)
    def second(self, suite_parameter):
        PHASE2.append("second")
        if _mark("second") < 2:
            assert False

    @test()
    def steady(self, suite_parameter):
        PHASE2.append("steady")


SETUPS = []


@Suite()
class ResetSetupFailsSuite:

    @beforeClass()
    def set_up(self):
        SETUPS.append("before_class")
        if len(SETUPS) > 1:
            raise RuntimeError("environment gone")

    @test(retry=Resets)
    def needs_setup(self):
        _mark("needs_setup")
        assert False


@Suite()
class ResetOnOneConditionSuite:

    @beforeClass()
    def set_up(self):
        PHASE2.append("before_class")

    @test(retry=ResetsOn503)
    def gets_503(self):
        if _mark("gets_503") < 2:
            raise RuntimeError("HTTP 503")

    @test(retry=ResetsOn503)
    def times_out(self):
        if _mark("times_out") < 2:
            raise TimeoutError("slow")


def _phase2(suites, **kwargs):
    _reset()
    del PHASE2[:]
    del SETUPS[:]
    Runner(suites).run(quiet=True, **kwargs)


def should_retry_has_the_last_word():
    _phase2([HookSuite])
    assert COUNTS["vetoed"] == 1, COUNTS
    assert ("should_retry", "RuntimeError", True, "vetoed") in PHASE2, PHASE2
    assert COUNTS["forced"] == 2, COUNTS  # ValueError isn't in retry_on, should_retry forced it


def before_retry_runs_before_each_retry():
    _phase2([HookSuite])
    assert [e for e in PHASE2 if e[0] == "before_retry"] == [("before_retry", "expired", 1, "prepared"),
                                                               ("before_retry", "expired", 2, "prepared")], PHASE2
    assert COUNTS["prepared"] == 3


def a_raising_before_retry_stops_retrying():
    _phase2([HookSuite])
    assert COUNTS["broken_prepare"] == 1, COUNTS
    test_object, _ = _variant(HookSuite, "broken_prepare")
    assert any("token service down" in str(r["when"]) for r in test_object.metrics.get_retries(None, None))


def max_time_stops_retrying():
    _phase2([HookSuite])
    assert 2 <= COUNTS["out_of_time"] <= 3, COUNTS  # 0.2s waits, 0.5s budget


def reset_class_sets_up_again_once_for_all_held_retries():
    _phase2([ResetSuite], test_multithreading_limit=3)
    first_pass = PHASE2[:PHASE2.index("after_class") + 1]
    assert sorted(first_pass[1:-1]) == ["first", "second", "steady"], PHASE2
    rest = PHASE2[len(first_pass):]
    assert rest[0] == "before_class" and rest[-1] == "after_class", PHASE2
    assert sorted(rest[1:-1]) == ["first", "second"] and rest.count("before_class") == 1, PHASE2  # one setup, both
    for name in ("first", "second"):
        test_object = _variant_param(ResetSuite, name, "admin")
        assert test_object["status"] == TestCategory.SUCCESS, (name, test_object["status"])


def reset_class_setup_failure_ignores_the_held_retry():
    _phase2([ResetSetupFailsSuite])
    assert SETUPS == ["before_class", "before_class"], SETUPS
    _, data = _variant(ResetSetupFailsSuite, "needs_setup")
    assert data["status"] == TestCategory.IGNORE, data["status"]
    assert "environment gone" in str(data["exceptions"][-1])


def reset_can_be_set_on_one_condition():
    _phase2([ResetOnOneConditionSuite])
    assert PHASE2.count("before_class") == 2, PHASE2  # the 503 reset the class, the timeout didn't
    assert COUNTS == {"gets_503": 2, "times_out": 2}, COUNTS


def bad_reset_and_max_time_are_rejected():
    for body, field in (("reset = 'suite'", "reset"), ("max_time = -1", "max_time")):
        try:
            exec("class Bad(RetryPolicy):\n    " + body, {"RetryPolicy": RetryPolicy})
        except BadParameters as error:
            assert field in str(error), str(error)
        else:
            raise AssertionError("accepted: " + body)


def _variant_param(suite_class, name, class_param):
    suite = Builder.get_execution_roster().get(suite_class)
    for test_object in suite.get_test_objects():
        if test_object.get_function_name() == name:
            return test_object.metrics.get_metrics()[class_param]["None"]
    raise AssertionError(name)


CHECKS = [each_condition_has_its_own_budget, no_retry_on_and_unmatched_failures_run_once,
          delays_are_waited_between_runs, backoff_doubles_up_to_max_delay,
          message_matches_the_raised_error_not_the_truncated_copy, instance_overrides_class_fields,
          chain_and_regex_match, on_retry_and_metrics_record_each_retry,
          suite_policy_applies_unless_the_test_sets_retry, plain_retry_fires_on_retry_without_a_policy,
          cancel_ends_the_wait_and_pool_slots_are_free_meanwhile, no_retry_flag_turns_a_policy_off,
          reports_show_the_retry, bad_policies_are_rejected_when_defined, mixing_a_policy_with_retry_on_is_rejected,
          should_retry_has_the_last_word, before_retry_runs_before_each_retry,
          a_raising_before_retry_stops_retrying, max_time_stops_retrying,
          reset_class_sets_up_again_once_for_all_held_retries, reset_class_setup_failure_ignores_the_held_retry,
          reset_can_be_set_on_one_condition, bad_reset_and_max_time_are_rejected]
