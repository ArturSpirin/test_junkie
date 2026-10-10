"""
Flaky tests (0.9a8): TestObject.is_flaky() / get_flaky() and the JSON report's "flaky", shared by both test paths:
tests/pytest/predeploy_tests/retry/test_flaky.py and tests/test_junkie/predeploy_tests/test_flaky.py
"""
import json
import os
import tempfile

from test_junkie.builder import Builder
from test_junkie.decorators import Suite, test
from test_junkie.retry import RetryPolicy
from test_junkie.runner import Runner

COUNTS = {}


def _mark(name):
    COUNTS[name] = COUNTS.get(name, 0) + 1
    return COUNTS[name]


class Twice(RetryPolicy):
    attempts = 2


@Suite()
class FlakyTests:

    @test(retry=2)
    def passes_second_time(self):
        if _mark("passes_second_time") < 2:
            assert False, "not yet"

    @test(retry=2)
    def errors_then_passes(self):
        if _mark("errors_then_passes") < 2:
            raise RuntimeError("connection reset")

    @test(retry=2)
    def solid(self):
        _mark("solid")

    @test(retry=2)
    def always_fails(self):
        _mark("always_fails")
        assert False, "never"

    @test(retry=3, parameters=["admin", "viewer"])
    def per_parameter(self, parameter):
        if parameter == "admin" and _mark("per_parameter_admin") < 3:
            assert False, "admin only"

    @test(retry=Twice)
    def by_policy(self):
        if _mark("by_policy") < 2:
            raise TimeoutError("slow")


@Suite(retry=2)
class SuitePassFlaky:

    @test()
    def recovers_on_the_next_pass(self):
        if _mark("recovers_on_the_next_pass") < 2:
            assert False, "first pass"


def _run(suites, **kwargs):
    COUNTS.clear()
    Runner(suites).run(quiet=True, **kwargs)


def _test(suite_class, name):
    for test_object in Builder.get_execution_roster().get(suite_class).get_test_objects():
        if test_object.get_function_name() == name:
            return test_object
    raise AssertionError(name)


def flaky_only_when_a_pass_followed_a_failure():
    _run([FlakyTests])
    assert _test(FlakyTests, "passes_second_time").is_flaky()
    assert _test(FlakyTests, "errors_then_passes").is_flaky()  # an error counts like a failure
    assert not _test(FlakyTests, "solid").is_flaky()
    assert not _test(FlakyTests, "always_fails").is_flaky()  # never passed: failed, not flaky


def flaky_is_per_parameter():
    _run([FlakyTests])
    test_object = _test(FlakyTests, "per_parameter")
    assert test_object.is_flaky("admin") and not test_object.is_flaky("viewer")


def get_flaky_lists_each_combination():
    _run([FlakyTests])
    assert _test(FlakyTests, "per_parameter").get_flaky() == [
        {"parameter": "admin", "suite_parameter": None, "passed_on_run": 3,
         "errors": ["AssertionError: admin only", "AssertionError: admin only"]}]
    assert _test(FlakyTests, "solid").get_flaky() == []
    assert _test(FlakyTests, "errors_then_passes").get_flaky()[0]["errors"] == ["RuntimeError: connection reset"]


def every_kind_of_retry_counts():
    _run([FlakyTests, SuitePassFlaky])
    assert _test(FlakyTests, "by_policy").is_flaky()  # a RetryPolicy
    assert _test(SuitePassFlaky, "recovers_on_the_next_pass").is_flaky()  # a suite retry pass


def json_report_marks_flaky():
    path = os.path.join(tempfile.mkdtemp(), "report.json")
    _run([FlakyTests], json_report=path)
    with open(path, encoding="utf-8") as doc:
        tests = json.load(doc)["suites"][0]["tests"]
    flaky = {(t["name"], t["parameter"]): t["flaky"] for t in tests}
    assert flaky[("passes_second_time", None)] is True and flaky[("solid", None)] is False, flaky
    assert flaky[("per_parameter", "admin")] is True and flaky[("per_parameter", "viewer")] is False, flaky
    assert flaky[("always_fails", None)] is False, flaky


def _xml_cases(**kwargs):
    from xml.etree.ElementTree import parse
    path = os.path.join(tempfile.mkdtemp(), "report.xml")
    _run([FlakyTests], xml_report=path, **kwargs)
    cases = {}
    for case in parse(path).getroot().iter("testcase"):
        cases.setdefault(case.get("name"), []).append(case)
    return cases


def xml_report_marks_flaky_runs():
    # Surefire's layout, which Jenkins, GitLab, CircleCI and flaky-test trackers read: a test that passed after
    # failing keeps a <flakyFailure>/<flakyError> per failed run, with the error and its stack trace
    cases = _xml_cases()
    case = cases["passes_second_time"][0]
    assert case.get("status") == "success" and case.find("failure") is None
    flaky = case.findall("flakyFailure")
    assert len(flaky) == 1 and flaky[0].get("type") == "AssertionError", [c.tag for c in case]
    assert flaky[0].get("message") == "not yet" and "not yet" in flaky[0].find("stackTrace").text
    errors = cases["errors_then_passes"][0].findall("flakyError")
    assert len(errors) == 1 and errors[0].get("type") == "RuntimeError" and errors[0].get("message") == "connection reset"
    assert list(cases["solid"][0]) == []
    per_parameter = sorted(len(c.findall("flakyFailure")) for c in cases["per_parameter"])
    assert per_parameter == [0, 2], per_parameter  # admin failed twice before passing, viewer passed at once


def xml_report_marks_reruns_of_failed_tests():
    # a test that never passed: the first failed run is <failure>, every retry after it is <rerunFailure>/<rerunError>
    case = _xml_cases()["always_fails"][0]
    failure = case.find("failure")
    assert failure is not None and failure.get("type") == "AssertionError" and failure.get("message") == "never"
    reruns = case.findall("rerunFailure")
    assert len(reruns) == 1 and "never" in reruns[0].find("stackTrace").text, [c.tag for c in case]
    assert case.find("flakyFailure") is None


CHECKS = [flaky_only_when_a_pass_followed_a_failure, flaky_is_per_parameter, get_flaky_lists_each_combination,
          every_kind_of_retry_counts, json_report_marks_flaky, xml_report_marks_flaky_runs,
          xml_report_marks_reruns_of_failed_tests]
