import threading
import time

from test_junkie.debugger import LogJunkie

# guards all of the bookkeeping below - suite threads, test threads and the main thread all read and write it.
# Re-entrant because the qualification checks call the other locked helpers.
_LOCK = threading.RLock()
# signalled whenever a suite/test thread finishes, so the scheduler wakes up right away instead of polling.
# _GENERATION counts those events: a waiter captures it *before* checking its condition, so a thread that finishes
# between the check and the wait is never missed
_CHANGED = threading.Condition(_LOCK)
_GENERATION = [0]


def _alive(thread):
    # `finished` is set right before the thread signals - is_alive() is still True at that point
    return thread is not None and not getattr(thread, "finished", False) and thread.is_alive()


def _join(thread):
    # an untimed join() can't be interrupted on Windows - Ctrl+C was only seen once the thread finished
    while thread.is_alive():
        thread.join(0.25)


def _signals_when_done(func):
    def target(*args):
        try:
            func(*args)
        finally:
            with _CHANGED:
                threading.current_thread().finished = True
                _GENERATION[0] += 1
                _CHANGED.notify_all()
    return target


class ParallelProcessor:

    # suite class -> {"thread": suite thread or None if the suite runs on the main thread,
    #                 "tests": [{"test": TestObject, "thread": test thread}, ...]}
    __PARALLELS = {}
    __REVERSE_PARALLEL_RESTRICTIONS = {}

    def __init__(self, settings):

        # one ParallelProcessor per run() - start from a clean slate instead of the previous run's threads
        with _LOCK:
            ParallelProcessor.__PARALLELS.clear()
            ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS.clear()
            ParallelProcessor.__GATE.update({"owner": None, "depth": 0, "active": 0})

        self.__test_limit = settings.test_thread_limit
        if self.__test_limit == 0 or self.__test_limit is None:
            LogJunkie.warn("Thread limit for tests cannot be 0 or None, "
                           "falling back to limit of 1 thread per test case.")
            self.__test_limit = 1

        self.__started = time.monotonic()  # Limiter.RAMP_UP grows the limits from here

        self.__suite_limit = settings.suite_thread_limit
        if self.__suite_limit == 0 or self.__suite_limit is None:
            LogJunkie.warn("Thread limit for suites cannot be 0 or None, "
                           "falling back to limit of 1 thread per test suite.")
            self.__suite_limit = 1

        LogJunkie.debug("=======================Parallel Processor Settings=============================")
        LogJunkie.debug(">> Suite level multi-threading enabled: {}".format(self.suite_multithreading()))
        LogJunkie.debug(">> Suite level multi-threading limit: {}".format(self.__suite_limit))
        LogJunkie.debug(">> Test level multi-threading enabled: {}".format(self.test_multithreading()))
        LogJunkie.debug(">> Test level multi-threading limit: {}".format(self.__test_limit))
        LogJunkie.debug("===============================================================================")

    # The run-wide gate for @test(parallelized=False). Every test run and suite hook counts as activity; the owner of
    # the gate (a suite thread running an exclusive test) waits for activity to drain, and nothing else starts until
    # it releases the gate. owner -> threading.get_ident() of the holder, depth -> re-entries by that holder
    __GATE = {"owner": None, "depth": 0, "active": 0}

    @staticmethod
    def __gate_closed_to_me():
        owner = ParallelProcessor.__GATE["owner"]
        return owner is not None and owner != threading.get_ident()

    class _Activity(object):
        """with ParallelProcessor.activity(cancel): a test run or a suite hook - waits while another thread holds the gate"""

        def __init__(self, cancel=None):
            self.__cancel = cancel

        def __enter__(self):
            with _CHANGED:
                while ParallelProcessor._ParallelProcessor__gate_closed_to_me():
                    if callable(self.__cancel) and self.__cancel():
                        break  # cancelled: let it through so it can record CANCEL instead of waiting forever
                    _CHANGED.wait(0.25)
                ParallelProcessor._ParallelProcessor__GATE["active"] += 1
            return self

        def __exit__(self, *exc):
            with _CHANGED:
                gate = ParallelProcessor._ParallelProcessor__GATE
                gate["active"] = max(0, gate["active"] - 1)  # a nested run (a run inside a test) resets the count
                _GENERATION[0] += 1
                _CHANGED.notify_all()
            return False

    @staticmethod
    def activity(cancel=None):
        return ParallelProcessor._Activity(cancel)

    @staticmethod
    def acquire_exclusive(cancel=None):
        """
        Closes the gate to every new test and hook in the run, then waits for what's running to finish. The caller then
        runs alone until release_exclusive(). Re-entrant for the holder.
        """
        me = threading.get_ident()
        with _CHANGED:
            gate = ParallelProcessor.__GATE
            if gate["owner"] == me:
                gate["depth"] += 1
                return
            while gate["owner"] is not None:
                if callable(cancel) and cancel():
                    break
                _CHANGED.wait(0.25)
            gate["owner"], gate["depth"] = me, 1
            while gate["active"] > 0:
                if callable(cancel) and cancel():
                    break
                _CHANGED.wait(0.25)

    @staticmethod
    def release_exclusive():
        with _CHANGED:
            gate = ParallelProcessor.__GATE
            if gate["owner"] != threading.get_ident():
                return
            gate["depth"] -= 1
            if gate["depth"] <= 0:
                gate["owner"], gate["depth"] = None, 0
                _GENERATION[0] += 1
                _CHANGED.notify_all()

    def suite_multithreading(self):

        return self.__suite_limit > 1

    def test_multithreading(self):

        return self.__test_limit > 1

    @staticmethod
    def __entry(suite_class):
        return ParallelProcessor.__PARALLELS.setdefault(suite_class, {"thread": None, "tests": []})

    @staticmethod
    def generation():
        """
        :return: INT, changes every time a suite/test thread finishes. Capture it before checking a condition and pass
                 it to wait_for_change() if the condition isn't met yet
        """
        with _LOCK:
            return _GENERATION[0]

    @staticmethod
    def wait_for_change(generation, timeout=0.25):
        """
        Blocks until a suite/test thread finishes after `generation` was captured (returns right away if one already
        has). The timeout is a safety net, and keeps the main thread waking up often enough to see Ctrl+C
        """
        with _CHANGED:
            if _GENERATION[0] == generation:
                _CHANGED.wait(timeout)

    @staticmethod
    def wait_while(condition):
        """
        Blocks while condition() is True, re-checking it each time a suite/test thread finishes
        """
        while True:
            generation = ParallelProcessor.generation()
            if not condition():
                return
            ParallelProcessor.wait_for_change(generation)

    @staticmethod
    def run_suite_in_a_thread(func, suite):
        thread = threading.Thread(target=_signals_when_done(func), args=(suite,), daemon=True)
        with _LOCK:
            # registered and started under the lock, so nobody can see (and join) a thread that isn't started yet
            ParallelProcessor.__entry(suite.get_class_object())["thread"] = thread
            thread.start()
        return thread

    @staticmethod
    def run_test_in_a_thread(func, suite, test, parameter, class_parameter, before_class_error, cancel):
        thread = threading.Thread(target=_signals_when_done(func), args=(suite, test, parameter, class_parameter,
                                                                         before_class_error, cancel), daemon=True)
        with _LOCK:
            # a test thread used to be registered *before* start() - a concurrent wait could join() it and crash
            # with "cannot join thread before it is started"
            ParallelProcessor.__entry(suite.get_class_object())["tests"].append({"test": test, "thread": thread})
            thread.start()
        return thread

    @staticmethod
    def wait_currently_active_suites_to_finish():
        with _LOCK:
            threads = [info["thread"] for info in ParallelProcessor.__PARALLELS.values() if info["thread"]]
        for thread in threads:  # joined outside the lock - suite threads need it to make progress
            _join(thread)

    @staticmethod
    def wait_currently_active_tests_to_finish(suite=None):
        """
        :param suite: SuiteObject, only wait for this suite's tests. None waits for every suite's tests.
        """
        with _LOCK:
            if suite is None:
                entries = list(ParallelProcessor.__PARALLELS.values())
            else:
                entries = [ParallelProcessor.__entry(suite.get_class_object())]
            threads = [test["thread"] for entry in entries for test in entry["tests"]]
        for thread in threads:
            _join(thread)

    def __ramped(self, limit):
        # wait_while() re-checks at least every 0.25 s, so a limit that grows with time is seen without a signal
        from test_junkie.objects import Limiter
        return Limiter.ramped(limit, time.monotonic() - self.__started)

    def suite_limit_reached(self):
        with _LOCK:
            active = sum(1 for info in ParallelProcessor.__PARALLELS.values() if _alive(info["thread"]))
        limit = self.__ramped(self.__suite_limit)
        if active >= limit:
            LogJunkie.debug("Suite limit: {}/{}".format(active, limit))
            return True
        return False

    def test_limit_reached(self):
        with _LOCK:
            active = 0
            for info in ParallelProcessor.__PARALLELS.values():
                # drop finished tests so we don't accumulate stale data - under the lock, so two suite threads
                # can't both remove the same entry (used to raise "list.remove(x): x not in list")
                info["tests"] = [test for test in info["tests"] if _alive(test["thread"])]
                active += len(info["tests"])
        limit = self.__ramped(self.__test_limit)
        if active >= limit:
            LogJunkie.debug("Test limit: {}/{}".format(active, limit))
            return True
        return False

    # conflicts_with=: the run's ConflictMap (set by Runner.run) and test function object -> reservations held
    __CONFLICTS = None
    __RESERVED = {}

    @staticmethod
    def set_conflicts(conflict_map):
        with _LOCK:
            ParallelProcessor.__CONFLICTS = conflict_map
            ParallelProcessor.__RESERVED.clear()

    def suite_qualifies(self, suite):
        """A suite named in another's conflicts_with (suite to suite) doesn't start while that suite's thread runs"""
        conflicts = ParallelProcessor.__CONFLICTS
        with _LOCK:
            for other in (conflicts.suite_conflicts(suite) if conflicts is not None else ()):
                info = ParallelProcessor.__PARALLELS.get(other, None)
                if info is not None and _alive(info["thread"]):
                    LogJunkie.debug("Suite: {} can't run while: {} is running.".format(suite.get_class_object(), other))
                    return False
        # waiting for a free slot happens outside the lock - the suites holding the slots need it to finish
        ParallelProcessor.wait_while(self.suite_limit_reached)
        return True

    @staticmethod
    def reserve(test, cancel=None):
        """
        Waits until no test it conflicts with holds a reservation, then takes one - checked and taken in one step, so two
        conflicting tests can't both get through. The caller holds it for the whole test (every parameter) and calls
        release(); each test thread started for it calls hold()/release() too.
        :return: (seconds waited, [names of the tests it waited for])
        """
        conflicts = ParallelProcessor.__CONFLICTS
        others = conflicts.conflicts(test) if conflicts is not None else set()
        key = test.get_function_object()
        started, blockers = time.monotonic(), []
        with _CHANGED:
            while True:
                busy = [other for other in others if ParallelProcessor.__RESERVED.get(other, 0) > 0]
                if not busy or (callable(cancel) and cancel()):
                    break
                for other in busy:
                    name = conflicts.name(other)
                    if name not in blockers:
                        blockers.append(name)
                _CHANGED.wait(0.25)
            ParallelProcessor.__RESERVED[key] = ParallelProcessor.__RESERVED.get(key, 0) + 1
        return time.monotonic() - started, blockers

    @staticmethod
    def hold(test):
        with _CHANGED:
            key = test.get_function_object()
            ParallelProcessor.__RESERVED[key] = ParallelProcessor.__RESERVED.get(key, 0) + 1

    @staticmethod
    def release(test):
        with _CHANGED:
            key = test.get_function_object()
            ParallelProcessor.__RESERVED[key] = max(0, ParallelProcessor.__RESERVED.get(key, 0) - 1)
            _GENERATION[0] += 1
            _CHANGED.notify_all()
