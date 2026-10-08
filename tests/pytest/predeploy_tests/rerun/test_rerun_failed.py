import pytest

from test_junkie.errors import BadParameters
from test_junkie.rerun import Rerun
from tests.junkie_suites import RerunFailedSuite as fixture


def test_rerun_from_report_runs_only_the_failed_parameter():
    calls, aggregator = fixture.run(rerun=fixture.report_with({("env_b", 2)}))
    # env_a has nothing to run again, so it isn't set up at all
    assert calls == ["beforeClass:env_b", "login:env_b:2", "afterClass:env_b"]
    assert aggregator.get_basic_report()["tests"]["total"] == 1  # what passed before isn't reported again


def test_rerun_accepts_a_rerun_object():
    calls, _ = fixture.run(rerun=Rerun.from_report(fixture.report_with({("env_a", 1), ("env_a", 3)})))
    assert calls == ["beforeClass:env_a", "login:env_a:1", "login:env_a:3", "afterClass:env_a"]


def test_retry_in_a_rerun_stays_on_the_rerun_parameters():
    path = fixture.report_with({("env_b", 2)})
    fixture.FAILING.add(("env_b", 2))
    calls, aggregator = fixture.run(rerun=path)
    assert calls == ["beforeClass:env_b", "login:env_b:2", "login:env_b:2", "afterClass:env_b"]
    assert aggregator.get_basic_report()["tests"]["fail"] == 1


def test_test_without_suite_parameter_reruns_once():
    calls, _ = fixture.run(rerun=fixture.report_with({("once", None)}))
    assert calls == ["beforeClass:env_a", "once", "afterClass:env_a"]


def test_changed_parameters_all_run():
    path = fixture.report_with({("changing", None)})
    fixture.CHANGING[:] = ["v2", "v3"]  # the parameter that failed is gone
    calls, _ = fixture.run(rerun=path)
    assert calls == ["beforeClass:env_a", "changing:v2", "changing:v3", "afterClass:env_a"]


def test_nothing_to_rerun_runs_nothing():
    from test_junkie.runner import Runner
    runner = Runner([fixture.RerunFailedSuite, fixture.RerunOtherSuite], quiet=True)
    aggregator = runner.run(rerun=fixture.report_with(set()))
    assert aggregator.get_basic_report()["tests"]["total"] == 0
    assert runner.exit_code == 0  # nothing failed, so nothing to run again is a pass


def test_rerun_built_in_code():
    fixture.reset()
    rerun = Rerun().add("RerunFailedSuite", "login", 3, "env_b").add("RerunOtherSuite", "other")
    calls, _ = fixture.run(rerun=rerun)
    assert calls == ["beforeClass:env_b", "login:env_b:3", "afterClass:env_b", "other"]


def test_includes_can_be_overridden():
    class EvenOnly(Rerun):
        def includes(self, suite, test, parameter=None, suite_parameter=None):
            return parameter % 2 == 0 and suite_parameter == "env_a"

    fixture.reset()
    calls, _ = fixture.run(rerun=EvenOnly().add("RerunFailedSuite", "login"))
    assert calls == ["beforeClass:env_a", "login:env_a:2", "afterClass:env_a"]


def test_report_that_cant_be_read():
    with pytest.raises(BadParameters, match="JSON report"):
        Rerun.from_report("no/such/report.json")


def test_rerun_of_the_wrong_type():
    with pytest.raises(BadParameters, match="needs a Rerun"):
        fixture.run(rerun=["login"])
