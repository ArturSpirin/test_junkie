"""
Group-rule failures and a mid-run cancel, with a listener that records which events fire. Shared by the pytest
and TJ test paths.
"""
from test_junkie.decorators import Suite, test, GroupRules, beforeGroup, afterGroup
from test_junkie.listener import Listener

EVENTS = []


class RecordingListener(Listener):

    def on_before_group_failure(self, **kwargs):
        EVENTS.append(("on_before_group_failure", type(kwargs.get("exception")).__name__))

    def on_before_group_error(self, **kwargs):
        EVENTS.append(("on_before_group_error", type(kwargs.get("exception")).__name__))

    def on_after_group_failure(self, **kwargs):
        EVENTS.append(("on_after_group_failure", type(kwargs.get("exception")).__name__))

    def on_after_group_error(self, **kwargs):
        EVENTS.append(("on_after_group_error", type(kwargs.get("exception")).__name__))

    def on_cancel(self, **kwargs):
        EVENTS.append(("on_cancel", kwargs["properties"]["jm"]["jto"].get_function_name()))


def _suite(name):
    return Suite(listener=RecordingListener)(type(name, (), {"a_test": test()(lambda self: None)}))


BeforeGroupFails = _suite("BeforeGroupFails")
BeforeGroupErrors = _suite("BeforeGroupErrors")
AfterGroupFails = _suite("AfterGroupFails")
AfterGroupErrors = _suite("AfterGroupErrors")


@GroupRules()
def listener_event_rules(rules):

    @beforeGroup([BeforeGroupFails])
    def before_fails():
        raise AssertionError("before group failed")

    @beforeGroup([BeforeGroupErrors])
    def before_errors():
        raise ValueError("before group errored")

    @afterGroup([AfterGroupFails])
    def after_fails():
        raise AssertionError("after group failed")

    @afterGroup([AfterGroupErrors])
    def after_errors():
        raise ValueError("after group errored")


RUNNER = []


@Suite(listener=RecordingListener)
class CancelMidRun:

    @test(priority=1)
    def first(self):
        RUNNER[0].cancel()

    @test(priority=2)
    def second(self):
        pass

    @test(priority=3)
    def third(self):
        pass


def run_checks():
    from test_junkie.runner import Runner

    expected = {BeforeGroupFails: ("on_before_group_failure", "AssertionError"),
                BeforeGroupErrors: ("on_before_group_error", "ValueError"),
                AfterGroupFails: ("on_after_group_failure", "AssertionError"),
                AfterGroupErrors: ("on_after_group_error", "ValueError")}
    for suite, event in expected.items():
        del EVENTS[:]
        Runner([suite], quiet=True).run()
        # the before-group events were documented but never fired
        assert EVENTS == [event], (suite.__name__, EVENTS)

    # Runner.cancel() mid-run used to raise TypeError for the remaining tests instead of cancelling them
    del EVENTS[:]
    del RUNNER[:]
    RUNNER.append(Runner([CancelMidRun], quiet=True))
    report = RUNNER[0].run().get_basic_report()["tests"]
    assert report["success"] == 1 and report["cancel"] == 2, report
    assert EVENTS == [("on_cancel", "second"), ("on_cancel", "third")], EVENTS
