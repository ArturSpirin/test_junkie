from test_junkie.runner import Runner
from tests.junkie_suites import RunnerReuseSuite as fixture
from tests.junkie_suites.RunnerReuseSuite import RunnerReuseSuite


def test_new_runner_instance_runs_group_rules_again():
    # group rule definitions were shared and consumed by the first Runner, so any later Runner in the same
    # process silently skipped @beforeGroup/@afterGroup
    assert fixture.run(Runner([RunnerReuseSuite], quiet=True)) == fixture.FULL_RUN
    assert fixture.run(Runner([RunnerReuseSuite], quiet=True)) == fixture.FULL_RUN


def test_same_runner_can_run_again():
    # run() consumed the Runner's suite list, so a second run() ran nothing
    runner = Runner([RunnerReuseSuite], quiet=True)
    assert fixture.run(runner) == fixture.FULL_RUN
    assert fixture.run(runner) == fixture.FULL_RUN


def test_run_arguments_do_not_leak_into_the_next_run():
    runner = Runner([RunnerReuseSuite], quiet=True)
    assert fixture.run(runner, tests=["test_a"]) == ["beforeGroup", "test_a", "afterGroup"]
    assert fixture.run(runner) == fixture.FULL_RUN


def test_cancel_applies_to_one_run_only():
    # cancel() before run() is supported (see on_class/test_cancel.py); it must not stick to later runs
    runner = Runner([RunnerReuseSuite], quiet=True)
    runner.cancel()
    assert "test_a" not in fixture.run(runner)
    assert fixture.run(runner) == fixture.FULL_RUN
