from test_junkie.console import expected_units
from test_junkie.constants import TestCategory
from test_junkie.rerun import Rerun
from tests.junkie_suites import SuiteParameterHookSuite as fixture
from tests.junkie_suites.SuiteParameterHookSuite import EveryTestPerParameterSuite, HookOnlySuite, \
    FlagWithoutParametersSuite


def test_with_the_flag_a_plain_test_runs_once_per_suite_parameter():
    calls, _, suite = fixture.run(EveryTestPerParameterSuite)
    assert sorted(c for c in calls if c[0] == "plain") == [("plain", "a"), ("plain", "b")]
    plain = fixture.live(suite, "plain")
    assert plain.get_status(None, "a") == TestCategory.SUCCESS
    assert plain.get_status(None, "b") == TestCategory.SUCCESS
    assert plain.get_status(None, None) is None


def test_with_the_flag_hooks_get_the_running_suite_parameter():
    calls, _, _ = fixture.run(EveryTestPerParameterSuite)
    before = [c[1] for c in calls if c[0] == "before"]
    after = [c[1] for c in calls if c[0] == "after"]
    assert sorted(before) == ["a"] * 3 + ["b"] * 3  # plain + with_params[1, 2], under each suite parameter
    assert sorted(after) == sorted(before)
    assert None not in before


def test_with_the_flag_meta_update_writes_to_the_running_slot():
    _, _, suite = fixture.run(EveryTestPerParameterSuite)
    plain = fixture.live(suite, "plain")
    assert plain.get_meta(None, "a")["seen"] == "a"
    assert plain.get_meta(None, "b")["seen"] == "b"


def test_with_the_flag_test_parameters_run_under_each_suite_parameter():
    calls, aggregator, suite = fixture.run(EveryTestPerParameterSuite)
    assert sorted(c for c in calls if c[0] == "with_params") == \
        [("with_params", "a", 1), ("with_params", "a", 2), ("with_params", "b", 1), ("with_params", "b", 2)]
    assert aggregator.get_basic_report()["tests"]["total"] == 6
    assert expected_units(suite) == 6


def test_with_the_flag_a_rerun_repeats_only_the_failed_suite_parameter():
    _, aggregator, _ = fixture.run(EveryTestPerParameterSuite, failing={"b"})
    assert aggregator.get_basic_report()["tests"]["fail"] == 1
    rerun = Rerun().add("EveryTestPerParameterSuite", "plain", suite_parameter="b")
    calls, aggregator, suite = fixture.run(EveryTestPerParameterSuite, rerun=rerun)
    assert [c for c in calls if c[0] == "plain"] == [("plain", "b")]
    assert aggregator.get_basic_report()["tests"]["total"] == 1
    assert expected_units(suite, rerun) == 1


def test_without_the_flag_a_plain_test_runs_once_and_hooks_get_none():
    calls, _, suite = fixture.run(HookOnlySuite)
    assert calls == [("before", None), ("plain", None), ("after", None)]
    assert fixture.live(suite, "plain").get_status(None, None) == TestCategory.SUCCESS
    assert expected_units(suite) == 1


def test_the_flag_does_nothing_without_suite_parameters():
    calls, aggregator, _ = fixture.run(FlagWithoutParametersSuite)
    assert calls == [("before", None), ("plain", None)]
    assert aggregator.get_basic_report()["tests"]["total"] == 1
