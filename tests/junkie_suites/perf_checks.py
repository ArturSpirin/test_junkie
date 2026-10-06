"""
Performance guards shared by the pytest and TJ test paths. They check structure and scaling rather than absolute
speed, so they hold on slow CI runners.
"""
import copy
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


CHECKS = [copies_are_cheap_and_independent, rules_still_get_independent_copies,
          runtime_scales_linearly_with_suite_size]
