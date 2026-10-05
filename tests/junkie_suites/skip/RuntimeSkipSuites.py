from test_junkie.decorators import Suite, test
from test_junkie.listener import Listener
from test_junkie.shortcuts import skip

# Module-level event log used by RuntimeSkipEventSuite tests.
_events = []


class _EventTracker(Listener):
    def on_skip(self, **kwargs): _events.append("skip")
    def on_success(self, **kwargs): _events.append("success")
    def on_complete(self, **kwargs): _events.append("complete")
    def on_in_progress(self, **kwargs): _events.append("in_progress")


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

    @test()
    def test_will_skip(self):
        skip()


@Suite()
class RuntimeSkipWithParamsSuite:

    @test(parameters=[1, 2, 3])
    def test_skip_on_param_2(self, parameter=None):
        if parameter == 2:
            skip("param 2 not supported")
