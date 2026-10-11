"""
Performance guards shared by the pytest and TJ test paths. They check structure and scaling rather than absolute
speed, so they hold on slow CI runners.
"""
import copy
import os
import time

from test_junkie.builder import Builder
from test_junkie.decorators import Suite, test
from test_junkie.rules import Rules


class TagMutatingRules(Rules):

    def before_test(self, **kwargs):
        kwargs["test"].get_tags().append("added_by_rule")


@Suite(rules=TagMutatingRules)
class CopiedSuite:

    @test(tags=["original"])
    def a(self):
        pass

    @test()
    def b(self):
        pass


def _suite_of(size, rules=None):
    def make(i):
        def body(self):
            pass
        body.__name__ = "t%04d" % i
        return test()(body)
    kwargs = {"rules": rules} if rules else {}
    return Suite(**kwargs)(type("ScalingSuite%d" % size, (), {"t%04d" % i: make(i) for i in range(size)}))


def _calls(size, rules=None):
    """
    Function calls (Python and builtin) one run of a `size`-test suite makes in this thread, counted by a
    `sys.setprofile` hook. A count, not a time: it comes out the same on a busy CI runner as on an idle machine.
    Not cProfile: on 3.12+ it is built on sys.monitoring, which sees every thread, so the live console thread's calls
    (as many as it gets ticks in, i.e. clock-dependent) would leak into the count
    """
    import sys
    from test_junkie.runner import Runner
    suite = _suite_of(size, rules)
    counted = [0]

    def count(frame, event, arg):
        if event == "call" or event == "c_call":
            counted[0] += 1

    previous = sys.getprofile()
    sys.setprofile(count)
    try:
        Runner([suite], quiet=True).run()
    finally:
        sys.setprofile(previous)
    return counted[0]


def _calls_per_added_test(low, high, rules=None):
    """
    Extra calls per added test between two suite sizes - fixed per-run costs cancel out
    """
    return (_calls(high, rules) - _calls(low, rules)) / (high - low)


def copies_are_cheap_and_independent():
    suite = Builder.get_execution_roster()[CopiedSuite]
    live = suite.get_test_objects()[0]
    clone = copy.deepcopy(live)
    assert clone is not live and clone.suite is live.suite and clone.metrics is live.metrics
    clone.get_tags().append("mutated")
    assert "mutated" not in live.get_tags()
    # copying a whole suite stays self-consistent: the copied tests point at the copied suite
    suite_clone = copy.deepcopy(suite)
    assert all(t.suite is suite_clone for t in suite_clone.get_test_objects())


def rules_still_get_independent_copies():
    from test_junkie.runner import Runner
    Runner([CopiedSuite], quiet=True).run()
    tags = Builder.get_execution_roster()[CopiedSuite].get_test_objects()[0].get_tags()
    assert "added_by_rule" not in tags, tags


def calls_scale_linearly_with_suite_size():
    """
    The calls each added test costs stay the same as the suite grows. Catches per-test work done through Python
    calls (the pre-0.9a5 suite deep-copy below); does NOT catch O(N) work inside a single C call (list.index, `in` on
    a list, sorted() of the whole roster once per test), which is one call however long it takes
    """
    # before 0.9a5 every test deep-copied the whole suite twice for the Rules hooks, so each added test cost more
    # the bigger the suite was (O(N^2) per run - 1,000 tests took ~55s). Counted in calls, not timed: a wall-clock
    # ratio failed on GitHub runners even as the best of 5 runs (3.4x), and the quadratic code is only ~6x here.
    # Linear code is 1.00x (+-0.01); the old code is 5.8x
    for rules in (None, TagMutatingRules):
        _calls(20, rules)  # warm-up: first-run imports and caches
        small = _calls_per_added_test(50, 100, rules)
        large = _calls_per_added_test(400, 500, rules)
        assert large < small * 1.5, \
            "each added test got {:.2f}x more expensive in a bigger suite ({:.0f} -> {:.0f} calls, rules={})".format(
                large / small, small, large, rules)


def scheduler_waits_without_polling():
    # the scheduler used to poll with time.sleep(0.2) (1s for prioritized suites) whenever a suite or test had to
    # wait - and once per pass over the suite queue even when nothing waited, so every run paid ~200ms. It now
    # wakes up when a thread finishes. Only sleeps called from inside test_junkie count (the tests sleep themselves)
    import sys
    from test_junkie.runner import Runner
    from tests.junkie_suites.parallel_restrictions import timeline
    from tests.junkie_suites.parallel_restrictions.SuiteRestrictionA import SuiteRestrictionA
    from tests.junkie_suites.parallel_restrictions.SuiteRestrictionB import SuiteRestrictionB
    from tests.junkie_suites.parallel_restrictions.TestRestrictionSuite import TestRestrictionSuite
    from tests.junkie_suites.parallel_restrictions.ThrottleSuite import ThrottleSuite

    package = os.path.dirname(os.path.abspath(sys.modules["test_junkie"].__file__))
    real_sleep, polls = time.sleep, []

    def recording_sleep(seconds):
        if seconds and os.path.abspath(sys._getframe(1).f_code.co_filename).startswith(package + os.sep):
            polls.append(seconds)
        real_sleep(seconds)

    time.sleep = recording_sleep
    try:
        timeline.reset()
        Runner([SuiteRestrictionA, SuiteRestrictionB], quiet=True).run(suite_multithreading_limit=2)
        Runner([ThrottleSuite, TestRestrictionSuite], quiet=True).run(test_multithreading_limit=2)
        Runner([CopiedSuite], quiet=True).run()
    finally:
        time.sleep = real_sleep
    assert len(timeline.events()) == 7, timeline.events()  # 1 + 1 restricted suite tests, 3 throttled, 2 restricted
    assert polls == [], polls


def runner_import_stays_lean():
    # importlib.metadata (~25ms, just for the version string), the HTML reporter, the CLI + colorama and
    # multiprocessing used to load on every `import test_junkie.runner` - none are needed to run tests
    import subprocess
    import sys
    import test_junkie
    root = os.path.dirname(os.path.dirname(os.path.abspath(test_junkie.__file__)))
    # only what the import itself adds - under `coverage run` the child already has coverage's own imports loaded
    probe = ("import sys; before = set(sys.modules); import test_junkie.runner; "
             "print(sorted(m for m in ('importlib.metadata', 'colorama', 'multiprocessing', 'test_junkie.cli.cli', "
             "'test_junkie.reporter.html_reporter') if m in sys.modules and m not in before))")
    loaded = subprocess.run([sys.executable, "-c", probe], cwd=root, capture_output=True, text=True, check=True)
    assert loaded.stdout.strip() == "[]", loaded.stdout + loaded.stderr
    version = subprocess.run([sys.executable, "-m", "test_junkie", "version"], cwd=root, capture_output=True,
                             text=True, env=dict(os.environ, NO_COLOR="1"))  # colored under GITHUB_ACTIONS
    assert version.stdout.startswith("Test Junkie {} ".format(test_junkie.__version__)), version.stdout


CHECKS = [copies_are_cheap_and_independent, rules_still_get_independent_copies,
          calls_scale_linearly_with_suite_size, scheduler_waits_without_polling, runner_import_stays_lean]
