"""
conflicts_with= (0.9a8; formerly pr=), shared by both test paths:
tests/pytest/predeploy_tests/test_conflicts.py and tests/test_junkie/predeploy_tests/test_conflicts.py
"""
import json
import os
import tempfile
import threading
import time
import warnings

from test_junkie.builder import Builder
from test_junkie.decorators import Suite, test
from test_junkie.errors import BadParameters
from test_junkie.runner import Runner

SPANS = []
_LOCK = threading.Lock()
WORK = 0.2


def _work(name):
    start = time.monotonic()
    time.sleep(WORK)
    with _LOCK:
        SPANS.append((name, start, time.monotonic()))


def _overlap(a_prefix, b_prefix):
    a = [s for s in SPANS if s[0].startswith(a_prefix)]
    b = [s for s in SPANS if s[0].startswith(b_prefix)]
    assert a and b, SPANS
    return [(x[0], y[0]) for x in a for y in b if x[1] < y[2] and y[1] < x[2]]


# -- the race: two suites in parallel, each starting with a test that conflicts with the other's ----------------------

@Suite()
class InventoryWriter:
    @test(conflicts_with=["InventoryReader.reads"])
    def writes(self):
        _work("writer")


@Suite()
class InventoryReader:
    @test()
    def reads(self):
        _work("reader")


# -- nothing slips in between a test's parameters --------------------------------------------------------------------

@Suite()
class Migrations:
    @test(parameters=[1, 2, 3])
    def migrate(self, parameter):
        _work("migrate:{}".format(parameter))


@Suite()
class Reports:
    @test(conflicts_with=[Migrations.migrate])
    def report(self):
        time.sleep(0.05)  # starts while migrate is between parameters
        _work("report")


# -- mixed targets: a test names a suite, a suite names a test ------------------------------------------------------

@Suite()
class Database:
    @test()
    def one(self):
        _work("db:one")

    @test()
    def two(self):
        _work("db:two")


@Suite()
class Backup:
    @test(conflicts_with=[Database])
    def backup(self):
        _work("backup")


@Suite(conflicts_with=["Database.two"])
class Cache:
    @test()
    def warm(self):
        _work("cache")


# -- old name ---------------------------------------------------------------------------------------------------------

@Suite()
class OldName:
    @test(pr=[InventoryReader.reads])
    def old(self):
        _work("old")


def _run(suites, **kwargs):
    del SPANS[:]
    Runner(suites).run(quiet=True, **kwargs)


def conflicting_tests_never_overlap_when_run_inline():
    for _ in range(3):
        _run([InventoryWriter, InventoryReader], suite_multithreading_limit=2, test_multithreading_limit=1)
        assert not _overlap("writer", "reader"), _overlap("writer", "reader")


def conflicting_tests_never_overlap_with_test_threads():
    for _ in range(3):
        _run([InventoryWriter, InventoryReader], suite_multithreading_limit=2, test_multithreading_limit=4,
             test_throttling=0.05)
        assert not _overlap("writer", "reader"), _overlap("writer", "reader")


def nothing_slips_in_between_parameters():
    _run([Migrations, Reports], suite_multithreading_limit=2, test_multithreading_limit=4)
    migrate = [s for s in SPANS if s[0].startswith("migrate")]
    first, last = min(s[1] for s in migrate), max(s[2] for s in migrate)
    report = [s for s in SPANS if s[0] == "report"][0]
    assert report[2] <= first or report[1] >= last, SPANS


def a_test_can_name_a_suite_and_a_suite_a_test():
    _run([Database, Backup, Cache], suite_multithreading_limit=3, test_multithreading_limit=4)
    assert not _overlap("backup", "db:"), _overlap("backup", "db:")
    assert not _overlap("cache", "db:two"), _overlap("cache", "db:two")


def pr_still_works_and_warns_once():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _run([OldName, InventoryReader], suite_multithreading_limit=2)
    assert not _overlap("old", "reader"), _overlap("old", "reader")
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning) and "conflicts_with" in str(w.message)]
    assert len(deprecations) == 1, [str(w.message) for w in caught]


def both_names_are_rejected():
    try:
        @Suite()
        class Both:
            @test(pr=[InventoryReader.reads], conflicts_with=[InventoryReader.reads])
            def both(self):
                pass
    except BadParameters as error:
        assert "conflicts_with" in str(error) and "pr" in str(error)
    else:
        raise AssertionError("pr= and conflicts_with= together were accepted")


def bad_targets_are_rejected_before_anything_runs():
    @Suite()
    class Unknown:
        @test(conflicts_with=["NoSuchSuite.nope"])
        def a(self):
            _work("unknown")

    @Suite()
    class Itself:
        @test(conflicts_with=["Itself.a"])
        def a(self):
            _work("itself")

    @Suite()
    class WrongType:
        @test(conflicts_with=[42])
        def a(self):
            _work("wrong")

    for suite, text in ((Unknown, "NoSuchSuite.nope"), (Itself, "itself"), (WrongType, "42")):
        del SPANS[:]
        try:
            Runner([suite]).run(quiet=True)
        except BadParameters as error:
            assert text in str(error), str(error)
        else:
            raise AssertionError("{} wasn't rejected".format(suite.__name__))
        assert SPANS == [], SPANS


def waits_are_shown():
    folder = tempfile.mkdtemp(prefix="tj_conflicts_")
    path = os.path.join(folder, "report.json")
    _run([InventoryWriter, InventoryReader], suite_multithreading_limit=2, json_report=path)
    with open(path, encoding="utf-8") as doc:
        tests = [t for s in json.load(doc)["suites"] for t in s["tests"]]
    waits = [t.get("conflict_waits") for t in tests if t.get("conflict_waits")]
    assert waits, tests
    assert waits[0][0]["seconds"] >= 0.1 and waits[0][0]["with"], waits


def tj_audit_conflicts_lists_the_pairs():
    import subprocess
    import sys
    import textwrap
    folder = tempfile.mkdtemp(prefix="tj_audit_conflicts_")
    path = os.path.join(folder, "conflict_suite.py")
    with open(path, "w", encoding="utf-8") as suite_file:
        suite_file.write(textwrap.dedent('''
            from test_junkie.decorators import Suite, test

            @Suite()
            class Writer:
                @test(conflicts_with=["Reader.reads"])
                def writes(self):
                    pass

            @Suite()
            class Reader:
                @test()
                def reads(self):
                    pass
        '''))
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = dict(os.environ, PYTHONPATH=root + os.pathsep + os.environ.get("PYTHONPATH", ""))
    result = subprocess.run([sys.executable, "-m", "test_junkie", "audit", "conflicts", "-s", path, "--json"],
                            capture_output=True, text=True, env=env, timeout=120)
    assert result.returncode == 0, (result.stdout[-1500:], result.stderr[-1500:])
    assert json.loads(result.stdout[result.stdout.index("{"):]) == {"conflicts": [["Reader.reads", "Writer.writes"]]},         result.stdout


CHECKS = [conflicting_tests_never_overlap_when_run_inline, conflicting_tests_never_overlap_with_test_threads,
          nothing_slips_in_between_parameters, a_test_can_name_a_suite_and_a_suite_a_test,
          pr_still_works_and_warns_once, both_names_are_rejected, bad_targets_are_rejected_before_anything_runs,
          waits_are_shown, tj_audit_conflicts_lists_the_pairs]


if __name__ == "__main__":
    for check in CHECKS:
        try:
            check()
            print("PASS", check.__name__)
        except Exception as error:
            print("FAIL", check.__name__, type(error).__name__, str(error)[:300])
