import pytest

from test_junkie.runner import Runner
from test_junkie.errors import TestListenerError as ListenerError
from tests.junkie_suites.parallel_restrictions import timeline
from tests.junkie_suites.parallel_restrictions.SuiteRestrictionA import SuiteRestrictionA
from tests.junkie_suites.parallel_restrictions.SuiteRestrictionB import SuiteRestrictionB
from tests.junkie_suites.parallel_restrictions.TestRestrictionSuite import TestRestrictionSuite
from tests.junkie_suites.parallel_restrictions.BadSuiteRestriction import BadSuiteRestriction
from tests.junkie_suites.parallel_restrictions.BadTestRestrictionSuite import BadTestRestrictionSuite
from tests.junkie_suites.parallel_restrictions.ThrottleSuite import ThrottleSuite
from tests.junkie_suites.parallel_restrictions.ParallelParamsSuite import ParallelParamsSuite
from tests.junkie_suites.parallel_restrictions.BrokenListener import BrokenListenerSuite
from tests.junkie_suites.parallel_restrictions.SuiteThrottleX import SuiteThrottleX
from tests.junkie_suites.parallel_restrictions.SuiteThrottleY import SuiteThrottleY
from tests.junkie_suites.parallel_restrictions.SuiteThrottleZ import SuiteThrottleZ


def setup_function():
    timeline.reset()


def test_suite_level_restriction_blocks_overlap():

    # B listed first so it starts before A's turn comes up - A then finds B already
    # alive via its own declared restriction (not just the automatic reverse one).
    runner = Runner([SuiteRestrictionB, SuiteRestrictionA])
    runner.run(suite_multithreading_limit=2)

    assert not timeline.any_overlap("suite_a", "suite_b")
    assert len(timeline.events()) == 2


def test_suite_level_thread_limit_caps_at_limit():

    runner = Runner([SuiteThrottleX, SuiteThrottleY, SuiteThrottleZ])
    runner.run(suite_multithreading_limit=2)

    assert len(timeline.events()) == 3
    assert timeline.max_simultaneous() == 2


def test_test_level_restriction_blocks_overlap():

    runner = Runner([TestRestrictionSuite])
    runner.run(test_multithreading_limit=2)

    assert not timeline.any_overlap("test_m", "test_n")
    assert len(timeline.events()) == 2


def test_bad_suite_restriction_raises():

    runner = Runner([BadSuiteRestriction])
    with pytest.raises(Exception, match="must be class objects"):
        runner.run(suite_multithreading_limit=2)


def test_bad_test_restriction_raises():

    runner = Runner([BadTestRestrictionSuite])
    with pytest.raises(Exception, match="must be function objects"):
        runner.run()


def test_throttle_caps_at_limit():

    runner = Runner([ThrottleSuite])
    runner.run(test_multithreading_limit=2)

    assert len(timeline.events()) == 3
    assert timeline.max_simultaneous() == 2


def test_parallelized_parameters_actually_overlap():

    runner = Runner([ParallelParamsSuite])
    runner.run(test_multithreading_limit=4)

    assert len(timeline.events()) == 4
    assert timeline.has_internal_overlap("parallel_params")


def test_broken_listener_raises_test_listener_error():

    runner = Runner([BrokenListenerSuite])
    with pytest.raises(ListenerError):
        runner.run()


def test_broken_listener_raises_test_listener_error_in_suite_threads():
    # an exception in a suite thread used to die with the thread - run() returned normally and the suite's
    # unfinished tests vanished from the results
    with pytest.raises(ListenerError):
        Runner([BrokenListenerSuite]).run(suite_multithreading_limit=2)


def test_broken_listener_raises_test_listener_error_in_test_threads():
    with pytest.raises(ListenerError):
        Runner([BrokenListenerSuite]).run(test_multithreading_limit=2)
