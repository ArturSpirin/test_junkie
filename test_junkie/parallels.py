import inspect
import threading
import time

from test_junkie.debugger import LogJunkie
from test_junkie.decorators import synchronized


class ParallelProcessor:

    __PARALLELS = {}
    __REVERSE_PARALLEL_RESTRICTIONS = {}

    def __init__(self, settings):

        # self.__test_limit = int(kwargs.get("test_multithreading_limit", 1))
        self.__test_limit = settings.test_thread_limit
        if self.__test_limit == 0 or self.__test_limit is None:
            LogJunkie.warn("Thread limit for tests cannot be 0 or None, "
                           "falling back to limit of 1 thread per test case.")
            self.__test_limit = 1

        # self.__suite_limit = int(kwargs.get("suite_multithreading_limit", 1))
        self.__suite_limit = settings.suite_thread_limit
        if self.__suite_limit == 0 or self.__suite_limit is None:
            LogJunkie.warn("Thread limit for suites cannot be 0 or None, "
                           "falling back to limit of 1 thread per test suite.")
            self.__suite_limit = 1

        print "Test: {} Suite: {}".format(self.__test_limit, self.__suite_limit)

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

    def test_limit_reached(self, parallels):

        active = 0
        for parallel in parallels:
            if parallel.isAlive():
                active += 1
        if active >= self.__test_limit:
            LogJunkie.debug("Test limit: {}/{}".format(active, self.__test_limit))
            return True
        return False

    @staticmethod
    def run_suite_in_a_thread(func, suite):
        thread = threading.Thread(target=func, args=(suite,))
        if suite not in ParallelProcessor.__PARALLELS:
            ParallelProcessor.__PARALLELS.update({suite.get_class_object(): {"thread": thread, "tests": []}})
        thread.start()
        return thread

    @staticmethod
    def wait_for_parallels_to_finish(parallels):
        for parallel in parallels:
            parallel.join()

    @staticmethod
    def run_test_in_a_thread(func, suite, test, parameter, class_parameter, before_class_error, cancel):
        thread = threading.Thread(target=func, args=(suite, test, parameter, class_parameter,
                                                     before_class_error, cancel))
        if suite not in ParallelProcessor.__PARALLELS:
            ParallelProcessor.__PARALLELS.update({suite.get_class_object(): {"thread": thread, "tests": []}})
        ParallelProcessor.__PARALLELS[suite.get_class_object()]["tests"].append({"test": test, "thread": thread})
        thread.start()
        return thread

    @staticmethod
    def get_active_parallels_count():
        active_parallels = 0
        for suite, data in ParallelProcessor.__PARALLELS.items():
            if data["thread"].isAlive():
                active_parallels += 1
        return active_parallels

    @staticmethod
    def get_active_test_parallels_count(suite_object):
        active_parallels = 0
        data = ParallelProcessor.__PARALLELS.get(suite_object.get_class_object(), None)
        if data is not None:
            for test in data["tests"]:
                if test["thread"].isAlive():
                    active_parallels += 1
        return active_parallels

    @staticmethod
    def get_active_parallels():
        return ParallelProcessor.__PARALLELS

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
            if ParallelProcessor.__PARALLELS.get(restriction, None) is not None:
                if ParallelProcessor.__PARALLELS[restriction]["thread"].isAlive():
                    LogJunkie.debug("Suite: {} can't run while: {} is running."
                                    .format(suite.get_class_object(), restriction))
                    return False
            return True

        def _passes_reverse_restriction():
            """
            If current suite is part of parallel restriction in another suite which is currently active, can't run it.
            :return: BOOLEAN
            """
            if suite.get_class_object() in ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS:
                reverse_suites = ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS[suite.get_class_object()]
                for reverse_suite in reverse_suites:
                    if ParallelProcessor.__PARALLELS.get(reverse_suite, None) is not None:
                        if ParallelProcessor.__PARALLELS[reverse_suite]["thread"].isAlive():
                            LogJunkie.debug("Suite: {} can't run while: {} is running due to reverse restriction."
                                            .format(suite.get_class_object(), reverse_suite))
                            return False
            return True

        if suite.get_parallel_restrictions():
            for restriction in suite.get_parallel_restrictions():
                if not inspect.isclass(restriction):
                    raise Exception("Parallel suite restrictions must be class objects. "
                                    "Instead suite: {} was restricted by a function: {}"
                                    .format(suite.get_class_object(), restriction))
                _build_reverse_restriction()
                if not _passes_restriction():
                    return False
        if not _passes_reverse_restriction():
            return False

        if self.__suite_limit is not None:
            while ParallelProcessor.get_active_parallels_count() >= self.__suite_limit:
                LogJunkie.debug("Suite level Thread limit reached! Active suites: {}/{}"
                                .format(ParallelProcessor.get_active_parallels_count(), self.__suite_limit))
                time.sleep(5)
        return True

    @synchronized(threading.Lock())
    def test_qualifies(self, suite, test):

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

        def _passes_restriction():
            """
            If current suite does not have any active restrictions, we can run it
            :return: BOOLEAN
            """
            for class_object, suite_mapping in list(ParallelProcessor.__PARALLELS.items()):
                for test_mapping in suite_mapping["tests"]:
                    if test_mapping["test"].get_function_object() in test.get_parallel_restrictions():
                        if test_mapping["thread"].isAlive():
                            return False
            return True

        def _passes_reverse_restriction():
            """
            If current suite is part of parallel restriction in another suite which is currently active, can't run it.
            :return: BOOLEAN
            """
            if test.get_function_object() in ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS:
                reverse_tests = ParallelProcessor.__REVERSE_PARALLEL_RESTRICTIONS[test.get_function_object()]
                for class_object, suite_mapping in list(ParallelProcessor.__PARALLELS.items()):
                    for test_mapping in suite_mapping["tests"]:
                        if test_mapping["test"].get_function_object() in reverse_tests:
                            if test_mapping["thread"].isAlive():
                                return False
            return True

        if test.get_parallel_restrictions():
            for restriction in test.get_parallel_restrictions():
                if not inspect.isfunction(restriction) and not inspect.ismethod(restriction):
                    raise Exception("Parallel test restrictions must be function objects. "
                                    "Instead test: {} was restricted by: {}"
                                    .format(test.get_function_name(), restriction))
                _build_reverse_restriction()
                if not _passes_restriction():
                    return False
        if not _passes_reverse_restriction():
            return False

        if self.__test_limit is not None:
            while ParallelProcessor.get_active_test_parallels_count(suite) >= self.__test_limit:
                LogJunkie.debug("Test level Thread limit reached! Active tests: {}/{}"
                                .format(ParallelProcessor.get_active_test_parallels_count(suite), self.__test_limit))
                time.sleep(5)
        return True
