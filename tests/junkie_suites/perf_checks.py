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


def _run_seconds(size, rules=None):
    from test_junkie.runner import Runner
    suite = _suite_of(size, rules)
    start = time.perf_counter()
    Runner([suite], quiet=True).run()
    return time.perf_counter() - start


def _marginal_ms_per_test(low, high, rules=None):
    """
    Extra time per added test between two suite sizes - fixed per-run costs cancel out
    """
    return (_run_seconds(high, rules) - _run_seconds(low, rules)) * 1000 / (high - low)


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


def runtime_scales_linearly_with_suite_size():
    # before 0.9a5 every test deep-copied the whole suite twice for the Rules hooks, so each added test cost more
    # the bigger the suite was (O(N^2) per run - 1,000 tests took ~55s). Linear code is ~1x here, the old code ~4.5x
    for rules in (None, TagMutatingRules):
        _run_seconds(20, rules)  # warm-up
        small = _marginal_ms_per_test(100, 300, rules)
        large = _marginal_ms_per_test(800, 1000, rules)
        assert large < max(small, 0.05) * 2.5, \
            "each added test got {:.1f}x more expensive in a bigger suite ({:.3f} -> {:.3f} ms, rules={})".format(
                large / small if small else float("inf"), small, large, rules)


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
                             text=True)
    assert version.stdout.startswith("Test Junkie {} ".format(test_junkie.__version__)), version.stdout


CHECKS = [copies_are_cheap_and_independent, rules_still_get_independent_copies,
          runtime_scales_linearly_with_suite_size, scheduler_waits_without_polling, runner_import_stays_lean]
