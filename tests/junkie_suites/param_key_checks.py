"""
Parameters that read the same (0.9a8, bug 8) and ids=, shared by both test paths:
tests/pytest/predeploy_tests/on_test/test_param_keys.py and tests/test_junkie/predeploy_tests/test_param_keys.py
"""
import json
import os
import tempfile

from test_junkie.builder import Builder
from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test
from test_junkie.runner import Runner

RAN = []


class Account(object):
    """Same text for every instance: the case ids= is for"""

    def __init__(self, login, good=True):
        self.login = login
        self.good = good

    def __str__(self):
        return "Account"


ALICE, BOB = Account("alice"), Account("bob", good=False)


@Suite()
class SameTextSuite:

    @test(parameters=[1, "1"])
    def clash(self, parameter):
        RAN.append(("clash", parameter))

    @test(parameters=[ALICE, BOB])
    def objects_clash(self, parameter):
        RAN.append(("objects_clash", parameter.login))

    @test()
    def sibling(self):
        RAN.append("sibling")


@Suite(parameters=[Account("x"), Account("y")])
class SameTextSuiteParameters:

    @test()
    def never(self, suite_parameter):
        RAN.append("never")


@Suite()
class IdsSuite:

    @test(parameters=[ALICE, BOB], ids=["alice", "bob"])
    def with_list(self, parameter):
        RAN.append(("with_list", parameter.login))
        assert parameter.good

    @test(parameters=[Account("carol"), Account("dave")], ids=lambda account: account.login)
    def with_function(self, parameter):
        RAN.append(("with_function", parameter.login))

    @test(parameters=[ALICE, BOB], ids=["only one"])
    def wrong_length(self, parameter):
        RAN.append("wrong_length")


def _test(suite, name):
    for test_object in Builder.get_execution_roster().get(suite).get_test_objects():
        if test_object.get_function_name() == name:
            return test_object
    raise AssertionError(name)


def _metrics(suite, name):
    return _test(suite, name).metrics.get_metrics()["None"]


def parameters_that_read_the_same_are_rejected():
    del RAN[:]
    Runner([SameTextSuite]).run(quiet=True)
    assert RAN == ["sibling"], RAN
    for name, text in (("clash", "'1'"), ("objects_clash", "'Account'")):
        data = _metrics(SameTextSuite, name)["None"]
        assert data["status"] == TestCategory.IGNORE, (name, data["status"])
        assert "read as {}".format(text) in str(data["exceptions"][-1]), str(data["exceptions"][-1])
        assert "ids=" in str(data["exceptions"][-1])


def suite_parameters_that_read_the_same_are_rejected():
    del RAN[:]
    Runner([SameTextSuiteParameters]).run(quiet=True)
    assert RAN == [], RAN
    suite = Builder.get_execution_roster().get(SameTextSuiteParameters)
    assert suite.get_status() == TestCategory.IGNORE
    assert "read as 'Account'" in str(suite.metrics.get_metrics()["initiation_error"])


def ids_name_parameters_that_read_the_same():
    del RAN[:]
    Runner([IdsSuite]).run(quiet=True)
    assert ("with_list", "alice") in RAN and ("with_list", "bob") in RAN, RAN
    data = _metrics(IdsSuite, "with_list")
    assert sorted(data) == ["alice", "bob"], sorted(data)
    assert data["alice"]["status"] == TestCategory.SUCCESS and data["bob"]["status"] == TestCategory.FAIL
    test_object = _test(IdsSuite, "with_list")
    assert test_object.get_status(ALICE, None) == TestCategory.SUCCESS
    assert test_object.get_status(BOB, None) == TestCategory.FAIL
    assert sorted(_metrics(IdsSuite, "with_function")) == ["carol", "dave"]


def ids_must_fit_the_parameters():
    del RAN[:]
    Runner([IdsSuite]).run(quiet=True)
    assert "wrong_length" not in RAN, RAN
    data = _metrics(IdsSuite, "wrong_length")["None"]
    assert data["status"] == TestCategory.IGNORE
    assert "1 labels for 2 parameters" in str(data["exceptions"][-1]), str(data["exceptions"][-1])


def reports_and_reruns_use_the_ids():
    del RAN[:]
    folder = tempfile.mkdtemp(prefix="tj_param_keys_")
    report = os.path.join(folder, "report.json")
    Runner([IdsSuite]).run(quiet=True, json_report=report)
    with open(report, encoding="utf-8") as doc:
        tests = json.load(doc)["suites"][0]["tests"]
    assert sorted(t["parameter"] for t in tests if t["name"] == "with_list") == ["alice", "bob"]
    del RAN[:]
    Runner([IdsSuite]).run(quiet=True, rerun=report)
    assert ("with_list", "bob") in RAN and ("with_list", "alice") not in RAN, RAN


CHECKS = [parameters_that_read_the_same_are_rejected, suite_parameters_that_read_the_same_are_rejected,
          ids_name_parameters_that_read_the_same, ids_must_fit_the_parameters, reports_and_reruns_use_the_ids]


if __name__ == "__main__":
    for check in CHECKS:
        try:
            check()
            print("PASS", check.__name__)
        except Exception as error:
            print("FAIL", check.__name__, type(error).__name__, str(error)[:400])
