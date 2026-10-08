import os
import tempfile

from test_junkie.decorators import Suite, test, beforeClass, afterClass

CALLS = []
FAILING = set()  # (suite parameter, parameter) of login that fail
CHANGING = ["v1"]  # parameters of changing_parameters, so a test can change them between runs


@Suite(parameters=["env_a", "env_b"])
class RerunFailedSuite:

    @beforeClass()
    def before_class(self, suite_parameter):
        CALLS.append("beforeClass:" + suite_parameter)

    @afterClass()
    def after_class(self, suite_parameter):
        CALLS.append("afterClass:" + suite_parameter)

    @test(parameters=[1, 2, 3], retry=2)
    def login(self, parameter, suite_parameter):
        CALLS.append("login:{}:{}".format(suite_parameter, parameter))
        assert (suite_parameter, parameter) not in FAILING

    @test()
    def once(self):
        # doesn't take the suite parameter - runs once, under env_a
        CALLS.append("once")
        assert ("once", None) not in FAILING

    @test(parameters=CHANGING)
    def changing_parameters(self, parameter):
        CALLS.append("changing:" + parameter)
        assert ("changing", None) not in FAILING


@Suite()
class RerunOtherSuite:

    @test()
    def other(self):
        CALLS.append("other")


def reset(failing=()):
    del CALLS[:]
    FAILING.clear()
    FAILING.update(failing)
    CHANGING[:] = ["v1"]


def run(**kwargs):
    """
    :return: (CALLS, Aggregator)
    """
    from test_junkie.runner import Runner
    del CALLS[:]
    aggregator = Runner([RerunFailedSuite, RerunOtherSuite], quiet=True).run(**kwargs)
    return list(CALLS), aggregator


def report_with(failing):
    """
    Runs everything with these failing and writes a JSON report
    :return: STRING, path to the report
    """
    reset(failing)
    path = os.path.join(tempfile.mkdtemp(), "report.json")
    run(json_report=path)
    FAILING.clear()
    return path
