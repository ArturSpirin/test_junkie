from test_junkie.decorators import Suite, test, beforeTest, afterTest
from test_junkie.listener import Listener
from test_junkie.rules import Rules
from test_junkie.shortcuts import skip

# Module-level event log used by RuntimeSkipEventSuite tests.
_events = []

# Hook calls logged by the afterTest-after-skip suites; tests clear it before each run.
_hooks = []


class _EventTracker(Listener):
    def on_skip(self, **kwargs): _events.append("skip")
    def on_success(self, **kwargs): _events.append("success")
    def on_complete(self, **kwargs): _events.append("complete")
    def on_in_progress(self, **kwargs): _events.append("in_progress")
    def on_error(self, **kwargs): _events.append("error")


@Suite()
class RuntimeSkipSuite:

    @test()
    def test_will_skip(self):
        skip()

    @test()
    def test_will_pass(self):
        pass


@Suite(retry=3)
class RuntimeSkipNoRetrySuite:

    call_count = 0

    @test()
    def test_skip_prevents_retry(self):
        RuntimeSkipNoRetrySuite.call_count += 1
        skip()


@Suite()
class RuntimeSkipMixedSuite:

    @test()
    def test_skip_a(self):
        skip()

    @test()
    def test_pass_b(self):
        pass

    @test()
    def test_skip_c(self):
        skip()

    @test()
    def test_pass_d(self):
        pass


@Suite(listener=_EventTracker)
class RuntimeSkipEventSuite:

    @afterTest()
    def after_test(self):
        _events.append("after_test")

    @test()
    def test_will_skip(self):
        skip()


@Suite()
class RuntimeSkipWithParamsSuite:

    @test(parameters=[1, 2, 3])
    def test_skip_on_param_2(self, parameter=None):
        if parameter == 2:
            skip("param 2 not supported")


@Suite()
class RuntimeSkipAfterTestSuite:
    """@beforeTest opens a resource, the test skips at runtime: @afterTest must still close it"""

    @beforeTest()
    def before_test(self):
        _hooks.append("open")

    @afterTest()
    def after_test(self):
        _hooks.append("close")

    @test()
    def test_will_skip(self):
        skip("not today")


class _AfterTestRules(Rules):

    def after_test(self, **kwargs):
        _hooks.append("rules.after_test")


@Suite(rules=_AfterTestRules)
class RuntimeSkipRulesAfterTestSuite:

    @test()
    def test_will_skip(self):
        skip()


@Suite(listener=_EventTracker)
class RuntimeSkipAfterTestFailsSuite:
    """@afterTest fails after a runtime skip: the test is an error, not a skip, and is not retried"""

    call_count = 0

    @afterTest()
    def after_test(self):
        raise Exception("cleanup failed")

    @test(retry=3)
    def test_will_skip(self):
        RuntimeSkipAfterTestFailsSuite.call_count += 1
        skip()


@Suite()
class BeforeTestFailsSuite:
    """@beforeTest fails partway: the test is an error and @afterTest does not run (as in unittest)"""

    @beforeTest()
    def before_test(self):
        _hooks.append("open")
        raise Exception("setup failed partway")

    @afterTest()
    def after_test(self):
        _hooks.append("close")

    @test()
    def test_never_runs(self):
        _hooks.append("body")
