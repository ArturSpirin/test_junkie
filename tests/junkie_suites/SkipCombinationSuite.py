"""
skip= callables that declare parameter and/or suite_parameter: asked once per combination, and skip only the
combinations they say. CALLS logs every test body that ran and every callable call; SKIPPED logs ON_SKIP
"""
from test_junkie.decorators import Suite, test
from test_junkie.listener import Listener
from test_junkie.runner import Runner

CALLS = []
SKIPPED = []


class _SkipTracker(Listener):
    def on_skip(self, **kwargs):
        properties = kwargs["properties"]
        SKIPPED.append((properties["jm"]["jto"].get_function_name(), properties["suite_meta"]["parameter"],
                        properties["test_meta"]["parameter"]))


def on_sqlite(suite_parameter):
    return suite_parameter == "sqlite"


def on_two(parameter):
    return parameter == 2


def on_sqlite_two(suite_parameter, parameter):
    CALLS.append(("callable", suite_parameter, parameter))
    return suite_parameter == "sqlite" and parameter == 2


def by_meta(meta, suite_parameter):
    return meta.get("db") == suite_parameter


def meta_only(meta):
    return meta.get("off") is True


def no_args():
    return False


def sees_suite_parameter(suite_parameter, parameter):
    CALLS.append(("once", suite_parameter, parameter))
    return parameter == 2


class _Rules:
    def on_pg(self, suite_parameter):
        return suite_parameter == "pg"


@Suite(parameters=["pg", "sqlite"], listener=_SkipTracker, retry=2)
class SkipCombinationSuite:

    @test(skip=on_sqlite)  # (a) suite_parameter only
    def by_suite_parameter(self, suite_parameter):
        CALLS.append(("by_suite_parameter", suite_parameter, None))

    @test(skip=on_two, parameters=[1, 2])  # (b) parameter only
    def by_parameter(self, suite_parameter, parameter):
        CALLS.append(("by_parameter", suite_parameter, parameter))

    @test(skip=on_sqlite_two, parameters=[1, 2])  # (c) both
    def by_both(self, suite_parameter, parameter):
        CALLS.append(("by_both", suite_parameter, parameter))

    @test(skip=by_meta, meta={"db": "pg"})  # (d) meta of the combination, plus suite_parameter
    def by_meta_and_suite_parameter(self, suite_parameter):
        CALLS.append(("by_meta_and_suite_parameter", suite_parameter, None))

    @test(skip=_Rules().on_pg)  # (e) bound method
    def by_method(self, suite_parameter):
        CALLS.append(("by_method", suite_parameter, None))

    @test(skip=meta_only, meta={"off": True})  # (f) meta-only, unchanged: skipped as a whole
    def by_meta_only(self):
        CALLS.append(("by_meta_only", None, None))

    @test(skip=no_args)  # (f) no-arg, unchanged
    def by_no_args(self, suite_parameter):
        CALLS.append(("by_no_args", suite_parameter, None))

    @test(skip=sees_suite_parameter, parameters=[1, 2])  # runs once, not per suite parameter
    def once(self, parameter):
        CALLS.append(("once_body", None, parameter))

    @test(skip=on_two, parameters=[1, 2])  # 2 is skipped, 1 fails the first time: the suite retries only 1
    def skipped_and_flaky(self, suite_parameter, parameter):
        CALLS.append(("skipped_and_flaky", suite_parameter, parameter))
        assert CALLS.count(("skipped_and_flaky", suite_parameter, parameter)) > 1


@Suite(parameters=["pg", "sqlite"], skip=on_sqlite)
class SuiteSkipPerCombinationSuite:

    @test()
    def never_runs(self):
        CALLS.append(("never_runs",))


def run(*suites):
    """
    :return: (Aggregator, {name: TestObject} of the run's tests)
    """
    CALLS.clear()
    SKIPPED.clear()
    runner = Runner(list(suites))
    aggregator = runner.run(quiet=True)
    tests = {t.get_function_name(): t for suite in runner.get_executed_suites() for t in suite.get_test_objects()}
    return aggregator, tests
