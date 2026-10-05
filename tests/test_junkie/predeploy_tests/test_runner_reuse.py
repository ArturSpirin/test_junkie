from test_junkie.decorators import Suite, test
from test_junkie.runner import Runner
from tests.junkie_suites import RunnerReuseSuite as fixture
from tests.junkie_suites.RunnerReuseSuite import RunnerReuseSuite


@Suite()
class RunnerReuseTestSuite:

    @test()
    def new_runner_instance_runs_group_rules_again(self):
        assert fixture.run(Runner([RunnerReuseSuite], quiet=True)) == fixture.FULL_RUN
        assert fixture.run(Runner([RunnerReuseSuite], quiet=True)) == fixture.FULL_RUN

    @test()
    def same_runner_can_run_again(self):
        runner = Runner([RunnerReuseSuite], quiet=True)
        assert fixture.run(runner) == fixture.FULL_RUN
        assert fixture.run(runner) == fixture.FULL_RUN

    @test()
    def run_arguments_do_not_leak_into_the_next_run(self):
        runner = Runner([RunnerReuseSuite], quiet=True)
        assert fixture.run(runner, tests=["test_a"]) == ["beforeGroup", "test_a", "afterGroup"]
        assert fixture.run(runner) == fixture.FULL_RUN

    @test()
    def cancel_applies_to_one_run_only(self):
        runner = Runner([RunnerReuseSuite], quiet=True)
        runner.cancel()
        assert "test_a" not in fixture.run(runner)
        assert fixture.run(runner) == fixture.FULL_RUN
