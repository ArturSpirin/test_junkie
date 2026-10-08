from test_junkie.decorators import Suite, test
from test_junkie.errors import BadParameters
from test_junkie.rerun import Rerun
from test_junkie.runner import Runner
from tests.junkie_suites import RerunFailedSuite as fixture


class EvenOnly(Rerun):

    def includes(self, suite, test, parameter=None, suite_parameter=None):
        return parameter % 2 == 0 and suite_parameter == "env_a"


@Suite()
class RerunFailedTestSuite:

    @test()
    def rerun_from_report_runs_only_the_failed_parameter(self):
        calls, aggregator = fixture.run(rerun=fixture.report_with({("env_b", 2)}))
        # env_a has nothing to run again, so it isn't set up at all
        assert calls == ["beforeClass:env_b", "login:env_b:2", "afterClass:env_b"]
        assert aggregator.get_basic_report()["tests"]["total"] == 1  # what passed before isn't reported again

    @test()
    def rerun_accepts_a_rerun_object(self):
        calls, _ = fixture.run(rerun=Rerun.from_report(fixture.report_with({("env_a", 1), ("env_a", 3)})))
        assert calls == ["beforeClass:env_a", "login:env_a:1", "login:env_a:3", "afterClass:env_a"]

    @test()
    def retry_in_a_rerun_stays_on_the_rerun_parameters(self):
        path = fixture.report_with({("env_b", 2)})
        fixture.FAILING.add(("env_b", 2))
        calls, aggregator = fixture.run(rerun=path)
        assert calls == ["beforeClass:env_b", "login:env_b:2", "login:env_b:2", "afterClass:env_b"]
        assert aggregator.get_basic_report()["tests"]["fail"] == 1

    @test()
    def test_without_suite_parameter_reruns_once(self):
        calls, _ = fixture.run(rerun=fixture.report_with({("once", None)}))
        assert calls == ["beforeClass:env_a", "once", "afterClass:env_a"]

    @test()
    def changed_parameters_all_run(self):
        path = fixture.report_with({("changing", None)})
        fixture.CHANGING[:] = ["v2", "v3"]  # the parameter that failed is gone
        calls, _ = fixture.run(rerun=path)
        assert calls == ["beforeClass:env_a", "changing:v2", "changing:v3", "afterClass:env_a"]

    @test()
    def nothing_to_rerun_runs_nothing(self):
        runner = Runner([fixture.RerunFailedSuite, fixture.RerunOtherSuite], quiet=True)
        aggregator = runner.run(rerun=fixture.report_with(set()))
        assert aggregator.get_basic_report()["tests"]["total"] == 0
        assert runner.exit_code == 0  # nothing failed, so nothing to run again is a pass

    @test()
    def rerun_built_in_code(self):
        fixture.reset()
        rerun = Rerun().add("RerunFailedSuite", "login", 3, "env_b").add("RerunOtherSuite", "other")
        calls, _ = fixture.run(rerun=rerun)
        assert calls == ["beforeClass:env_b", "login:env_b:3", "afterClass:env_b", "other"]

    @test()
    def includes_can_be_overridden(self):
        fixture.reset()
        calls, _ = fixture.run(rerun=EvenOnly().add("RerunFailedSuite", "login"))
        assert calls == ["beforeClass:env_a", "login:env_a:2", "afterClass:env_a"]

    @test()
    def report_that_cant_be_read(self):
        try:
            Rerun.from_report("no/such/report.json")
            raise AssertionError("expected BadParameters")
        except BadParameters as error:
            assert "JSON report" in str(error)

    @test()
    def rerun_of_the_wrong_type(self):
        try:
            fixture.run(rerun=["login"])
            raise AssertionError("expected BadParameters")
        except BadParameters as error:
            assert "needs a Rerun" in str(error)
