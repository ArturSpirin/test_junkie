from test_junkie.decorators import Suite, test, beforeTest
from test_junkie.errors import TestListenerError as ListenerError
from test_junkie.runner import Runner
from tests.junkie_suites.parallel_restrictions import timeline
from tests.junkie_suites.parallel_restrictions.BadSuiteRestriction import BadSuiteRestriction
from tests.junkie_suites.parallel_restrictions.BadTestRestrictionSuite import BadTestRestrictionSuite
from tests.junkie_suites.parallel_restrictions.BrokenListener import BrokenListenerSuite
from tests.junkie_suites.parallel_restrictions import StressSuites
from tests.junkie_suites.parallel_restrictions.ParallelParamsSuite import ParallelParamsSuite
from tests.junkie_suites.parallel_restrictions.SuiteRestrictionA import SuiteRestrictionA
from tests.junkie_suites.parallel_restrictions.SuiteRestrictionB import SuiteRestrictionB
from tests.junkie_suites.parallel_restrictions.SuiteThrottleX import SuiteThrottleX
from tests.junkie_suites.parallel_restrictions.SuiteThrottleY import SuiteThrottleY
from tests.junkie_suites.parallel_restrictions.SuiteThrottleZ import SuiteThrottleZ
from tests.junkie_suites.parallel_restrictions.TestRestrictionSuite import TestRestrictionSuite
from tests.junkie_suites.parallel_restrictions.ThrottleSuite import ThrottleSuite


@Suite()
class ParallelRestrictionsSuite:

    @beforeTest()
    def reset(self):
        timeline.reset()

    @test()
    def suite_level_restriction_blocks_overlap(self):
        runner = Runner([SuiteRestrictionB, SuiteRestrictionA])
        runner.run(suite_multithreading_limit=2)
        assert not timeline.any_overlap("suite_a", "suite_b")
        assert len(timeline.events()) == 2

    @test()
    def suite_level_thread_limit_caps_at_limit(self):
        runner = Runner([SuiteThrottleX, SuiteThrottleY, SuiteThrottleZ])
        runner.run(suite_multithreading_limit=2)
        assert len(timeline.events()) == 3
        assert timeline.max_simultaneous() == 2

    @test()
    def test_level_restriction_blocks_overlap(self):
        runner = Runner([TestRestrictionSuite])
        runner.run(test_multithreading_limit=2)
        assert not timeline.any_overlap("test_m", "test_n")
        assert len(timeline.events()) == 2

    @test()
    def bad_suite_restriction_raises(self):
        raised = False
        try:
            Runner([BadSuiteRestriction]).run(suite_multithreading_limit=2)
        except Exception as e:
            raised = True
            assert "must be class objects" in str(e)
        assert raised

    @test()
    def bad_test_restriction_raises(self):
        raised = False
        try:
            Runner([BadTestRestrictionSuite]).run()
        except Exception as e:
            raised = True
            assert "must be function objects" in str(e)
        assert raised

    @test()
    def throttle_caps_at_limit(self):
        runner = Runner([ThrottleSuite])
        runner.run(test_multithreading_limit=2)
        assert len(timeline.events()) == 3
        assert timeline.max_simultaneous() == 2

    @test()
    def parallelized_parameters_actually_overlap(self):
        runner = Runner([ParallelParamsSuite])
        runner.run(test_multithreading_limit=4)
        assert len(timeline.events()) == 4
        assert timeline.has_internal_overlap("parallel_params")

    @test()
    def broken_listener_raises_test_listener_error(self):
        raised = False
        try:
            Runner([BrokenListenerSuite]).run()
        except ListenerError:
            raised = True
        assert raised

    @test()
    def broken_listener_raises_test_listener_error_in_suite_threads(self):
        # an exception in a suite thread used to die with the thread - run() returned normally and the suite's
        # unfinished tests vanished from the results
        try:
            Runner([BrokenListenerSuite]).run(suite_multithreading_limit=2)
            raise AssertionError("Expected TestListenerError from a suite thread")
        except ListenerError:
            pass

    @test()
    def broken_listener_raises_test_listener_error_in_test_threads(self):
        try:
            Runner([BrokenListenerSuite]).run(test_multithreading_limit=2)
            raise AssertionError("Expected TestListenerError from a test thread")
        except ListenerError:
            pass

    @test()
    def suite_and_test_threading_stress(self):
        violations, incomplete_rounds = StressSuites.run(rounds=8)
        assert violations == []
        assert incomplete_rounds == 0
