"""
@test(parallelized=False) runs alone (0.9a8, bug 4), shared by both test paths:
tests/pytest/predeploy_tests/test_exclusive_tests.py and tests/test_junkie/predeploy_tests/test_exclusive_tests.py
"""
import threading
import time

from test_junkie.constants import TestOrder
from test_junkie.decorators import Suite, test, beforeClass
from test_junkie.errors import BadParameters
from test_junkie.retry import RetryPolicy
from test_junkie.runner import Runner

SPANS = []  # (name, start, end)
_LOCK = threading.Lock()
WORK = 0.15


def _work(name):
    start = time.monotonic()
    time.sleep(WORK)
    with _LOCK:
        SPANS.append((name, start, time.monotonic()))


def _overlaps(alone_prefix):
    """every span that overlaps a span whose name starts with alone_prefix (other than itself)"""
    alone = [s for s in SPANS if s[0].startswith(alone_prefix)]
    assert alone, SPANS
    bad = []
    for name, start, end in alone:
        for other, o_start, o_end in SPANS:
            if other == name:
                continue
            if o_start < end and o_end > start:
                bad.append((other, name))
    return bad


@Suite()
class OneSuite:
    @test(priority=1)
    def a(self):
        _work("a")

    @test(priority=2, parallelized=False)
    def alone(self):
        _work("alone")

    @test(priority=3)
    def b(self):
        _work("b")

    @test(priority=4)
    def c(self):
        _work("c")


@Suite(order=TestOrder.ALPHABETICAL)
class AlphabeticalSuite:
    @test()
    def a_first(self):
        _work("a_first")

    @test(parallelized=False)
    def b_alone(self):
        _work("alone:b")

    @test()
    def c_after(self):
        _work("c_after")

    @test()
    def d_after(self):
        _work("d_after")


@Suite()
class ExclusiveSuite:
    @test(parallelized=False)
    def alone(self):
        _work("alone:x")


@Suite()
class BusySuite:
    @beforeClass()
    def set_up(self):
        _work("busy:before_class")

    @test()
    def one(self):
        _work("busy:one")

    @test()
    def two(self):
        _work("busy:two")

    @test()
    def three(self):
        _work("busy:three")


@Suite()
class ParameterSuite:
    @test(parameters=[1, 2, 3], parallelized=False)
    def alone(self, parameter):
        _work("alone:p{}".format(parameter))

    @test()
    def other(self):
        _work("other")

    @test()
    def another(self):
        _work("another")


class ResetOnce(RetryPolicy):
    attempts = 2
    reset = "class"


@Suite()
class ResetAloneSuite:
    runs = []

    @test(parallelized=False, retry=ResetOnce)
    def alone(self):
        ResetAloneSuite.runs.append(1)
        _work("alone:run{}".format(len(ResetAloneSuite.runs)))
        assert len(ResetAloneSuite.runs) > 1, "fails the first time"


@Suite()
class ManyShortSuite:
    pass


for _index in range(15):
    def _short(self, _name="short{}".format(_index)):
        _work(_name)
    _short.__name__ = "short{}".format(_index)
    setattr(ManyShortSuite, _short.__name__, test()(_short))
ManyShortSuite = Suite()(ManyShortSuite)


def _run(suites, **kwargs):
    del SPANS[:]
    Runner(suites).run(quiet=True, **kwargs)


def alone_within_one_suite():
    _run([OneSuite], test_multithreading_limit=4)
    assert not _overlaps("alone"), _overlaps("alone")
    assert len(SPANS) == 4, SPANS


def alone_with_alphabetical_order():
    _run([AlphabeticalSuite], test_multithreading_limit=4)
    assert not _overlaps("alone"), _overlaps("alone")


def alone_across_parallel_suites():
    for _ in range(3):  # the race needs the suites to line up; a few rounds make that likely
        _run([BusySuite, ExclusiveSuite], test_multithreading_limit=4, suite_multithreading_limit=2)
        assert not _overlaps("alone"), _overlaps("alone")
        assert len(SPANS) == 5, SPANS


def nothing_slips_in_between_its_parameters():
    _run([ParameterSuite], test_multithreading_limit=4)
    spans = sorted(s for s in SPANS if s[0].startswith("alone"))
    first, last = min(s[1] for s in spans), max(s[2] for s in spans)
    others = [s for s in SPANS if not s[0].startswith("alone")]
    assert all(end <= first or start >= last for _, start, end in others), SPANS


def parallelized_parameters_contradicts_parallelized_false():
    try:
        @Suite()
        class Contradiction:
            @test(parameters=[1, 2], parallelized=False, parallelized_parameters=True)
            def both(self, parameter):
                pass
    except BadParameters as error:
        assert "parallelized_parameters" in str(error)
    else:
        raise AssertionError("parallelized=False with parallelized_parameters=True was accepted")


def a_reset_retry_of_an_exclusive_test_runs_alone_too():
    # the retry held by reset="class" ran without the exclusive lock, so other suites' tests overlapped it
    ResetAloneSuite.runs = []
    _run([ResetAloneSuite, ManyShortSuite], test_multithreading_limit=4, suite_multithreading_limit=2)
    assert len(ResetAloneSuite.runs) == 2, ResetAloneSuite.runs
    assert not _overlaps("alone"), _overlaps("alone")


CHECKS = [alone_within_one_suite, alone_with_alphabetical_order, alone_across_parallel_suites,
          nothing_slips_in_between_its_parameters, parallelized_parameters_contradicts_parallelized_false,
          a_reset_retry_of_an_exclusive_test_runs_alone_too]


if __name__ == "__main__":
    for check in CHECKS:
        try:
            check()
            print("PASS", check.__name__)
        except Exception as error:
            print("FAIL", check.__name__, type(error).__name__, str(error)[:300])
