import inspect
import threading

from test_junkie.constants import DocumentationLinks
from test_junkie.debugger import LogJunkie
from test_junkie.errors import BadParameters

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

        self.__test_limit = settings.test_thread_limit
        if self.__test_limit == 0 or self.__test_limit is None:
            LogJunkie.warn("Thread limit for tests cannot be 0 or None, "
                           "falling back to limit of 1 thread per test case.")
            self.__test_limit = 1

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
    def wait_for_change(generation, timeout=1.0):
        """
        Blocks until a suite/test thread finishes after `generation` was captured (returns right away if one already
        has). The timeout is only a safety net - every state change the scheduler waits on comes from a thread finishing
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
        thread = threading.Thread(target=_signals_when_done(func), args=(suite,))
        with _LOCK:
            # registered and started under the lock, so nobody can see (and join) a thread that isn't started yet
            ParallelProcessor.__entry(suite.get_class_object())["thread"] = thread
            thread.start()
        return thread

    @staticmethod
    def run_test_in_a_thread(func, suite, test, parameter, class_parameter, before_class_error, cancel):
        thread = threading.Thread(target=_signals_when_done(func), args=(suite, test, parameter, class_parameter,
                                                                         before_class_error, cancel))
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
            thread.join()

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
            thread.join()

    def suite_limit_reached(self):
        with _LOCK:
            active = sum(1 for info in ParallelProcessor.__PARALLELS.values() if _alive(info["thread"]))
        if active >= self.__suite_limit:
            LogJunkie.debug("Suite limit: {}/{}".format(active, self.__suite_limit))
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
        if active >= self.__test_limit:
            LogJunkie.debug("Test limit: {}/{}".format(active, self.__test_limit))
            return True
        return False

    def suite_qualifies(self, suite):

        def _build_reverse_restriction():
            """
            Bidirectional parallel restriction will be automatically added.
            If suite `A` is restricted to run when suite `B` is running - suite `B` will be automatically restricted
            to run when suite `A` is running
            :return: None
            """
            if restriction not in ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS:
                ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS.update({restriction: [suite.get_class_object()]})
            elif suite.get_class_object() not in ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS[restriction]:
                ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS[restriction].append(suite.get_class_object())
            else:
                return  # if nothing to add, return - to avoid logging
            LogJunkie.debug("Added reverse restriction! {} will not be processed while {} is running"
                            .format(restriction, suite.get_class_object()))

        def _passes_restriction():
            """
            If current suite does not have any active restrictions, we can run it
            :return: BOOLEAN
            """
            info = ParallelProcessor.__PARALLELS.get(restriction, None)
            if info is not None and _alive(info["thread"]):
                LogJunkie.debug("Suite: {} can't run while: {} is running."
                                .format(suite.get_class_object(), restriction))
                return False
            return True

        def _passes_reverse_restriction():
            """
            If current suite is part of parallel restriction in another suite which is currently active, can't run it.
            :return: BOOLEAN
            """
            for reverse_suite in ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS.get(suite.get_class_object(), []):
                info = ParallelProcessor.__PARALLELS.get(reverse_suite, None)
                if info is not None and _alive(info["thread"]):
                    LogJunkie.debug("Suite: {} can't run while: {} is running due to reverse restriction."
                                    .format(suite.get_class_object(), reverse_suite))
                    return False
            return True

        with _LOCK:
            if suite.get_parallel_restrictions():
                for restriction in suite.get_parallel_restrictions():
                    if not inspect.isclass(restriction):
                        raise BadParameters("Parallel suite restrictions must be class objects decorated with "
                                            "@Suite(). Suite {} received a non-class restriction: {!r} (type: {}). "
                                            "See documentation: {}"
                                            .format(suite.get_class_object(), restriction,
                                                    type(restriction).__name__, DocumentationLinks.THREADING))
                    _build_reverse_restriction()
                    if not _passes_restriction():
                        return False
            if not _passes_reverse_restriction():
                return False

        # waiting for a free slot happens outside the lock - the suites holding the slots need it to finish
        ParallelProcessor.wait_while(self.suite_limit_reached)
        return True

    def test_qualifies(self, test):

        def _build_reverse_restriction():
            """
            Bidirectional parallel restriction will be automatically added.
            If suite `A` is restricted to run when suite `B` is running - suite `B` will be automatically restricted
            to run when suite `A` is running
            :return: None
            """
            if restriction not in ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS:
                ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS.update({restriction: [test.get_function_object()]})
            elif test.get_function_object() not in ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS[restriction]:
                ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS[restriction].append(test.get_function_object())
            else:
                return  # if nothing to add, return - to avoid logging
            LogJunkie.debug("Added reverse test restriction! {} will not be processed while test: {} is running"
                            .format(restriction, test.get_function_object()))

        def _running_tests():
            return [test_mapping for suite_mapping in ParallelProcessor.__PARALLELS.values()
                    for test_mapping in suite_mapping["tests"] if _alive(test_mapping["thread"])]

        def _passes_restriction():
            """
            If current test does not have any active restrictions, we can run it
            :return: BOOLEAN
            """
            return not any(test_mapping["test"].get_function_object() in test.get_parallel_restrictions()
                           for test_mapping in _running_tests())

        def _passes_reverse_restriction():
            """
            If current test is part of parallel restriction in another test which is currently active, can't run it.
            :return: BOOLEAN
            """
            reverse_tests = ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS.get(test.get_function_object(), [])
            return not any(test_mapping["test"].get_function_object() in reverse_tests
                           for test_mapping in _running_tests())

        with _LOCK:
            if test.get_parallel_restrictions():
                for restriction in test.get_parallel_restrictions():
                    if not inspect.isfunction(restriction) and not inspect.ismethod(restriction):
                        raise BadParameters("Parallel test restrictions must be function objects decorated with "
                                            "@test(). Test {} received a non-function restriction: {!r} (type: {}). "
                                            "See documentation: {}"
                                            .format(test.get_function_name(), restriction,
                                                    type(restriction).__name__, DocumentationLinks.THREADING))
                    _build_reverse_restriction()
                    if not _passes_restriction():
                        return False
            return _passes_reverse_restriction()
