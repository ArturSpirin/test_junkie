"""
Many short tests across several suites, run with both suite- and test-level threading. Each suite counts its
tests in flight; @afterClass records a violation if any are still running (i.e. the suite was finished before
its test threads were). Used to shake out races in parallels.py.
"""
import random
import threading
import time

from test_junkie.decorators import Suite, test, afterClass

SUITE_COUNT = 6
TESTS_PER_SUITE = 8

_LOCK = threading.Lock()
VIOLATIONS = []
COMPLETED = []


def _make_suite(index):
    in_flight = {"count": 0}

    def make_test(name):
        def body(self):
            with _LOCK:
                in_flight["count"] += 1
            time.sleep(random.uniform(0, 0.004))
            with _LOCK:
                in_flight["count"] -= 1
                COMPLETED.append((index, name))
        body.__name__ = name
        return test()(body)

    def after_class(self):
        with _LOCK:
            if in_flight["count"]:
                VIOLATIONS.append("StressSuite{}: afterClass ran with {} test(s) still running"
                                  .format(index, in_flight["count"]))

    namespace = {"t{}".format(i): make_test("t{}".format(i)) for i in range(TESTS_PER_SUITE)}
    namespace["after_class"] = afterClass()(after_class)
    return Suite()(type("StressSuite{}".format(index), (), namespace))


STRESS_SUITES = [_make_suite(index) for index in range(SUITE_COUNT)]


def run(rounds=15):
    """
    :return: (LIST of violations, number of rounds where not every test completed)
    """
    from test_junkie.runner import Runner
    del VIOLATIONS[:]
    incomplete_rounds = 0
    for _ in range(rounds):
        del COMPLETED[:]
        Runner(list(STRESS_SUITES), quiet=True).run(suite_multithreading_limit=3, test_multithreading_limit=4)
        if len(COMPLETED) != SUITE_COUNT * TESTS_PER_SUITE:
            incomplete_rounds += 1
    return list(VIOLATIONS), incomplete_rounds
