import copy
import inspect
import threading
import time
import traceback

from test_junkie.constants import SuiteCategory, TestCategory, Event
from test_junkie.debugger import LogJunkie
from test_junkie.decorators import DecoratorType, synchronized
from test_junkie.errors import ConfigError, TestJunkieExecutionError, TestListenerError
from test_junkie.listener import Listener
from test_junkie.metrics import Aggregator, ResourceMonitor
from test_junkie.parallels import ParallelProcessor
from test_junkie.builder import Builder
from test_junkie.reporter.reporter import Reporter


class Runner:

    __STATS = {}

    def __init__(self, suites, **kwargs):

        self.__stats = {}

        self.__suites = suites
        if not isinstance(self.__suites, list):
            self.__suites = [self.__suites]

        self.__suites = self.__prioritize(suites=self.__suites)
        for suite in self.__suites:
            suite_object = Builder.get_execution_roster().get(suite, None)
            suite_object.update_test_objects(self.__prioritize(suite_object=suite_object))
            Runner.__process_owners(suite_object)

        self.__kwargs = kwargs

        self.__processor = None
        self.__run_config = {}

        self.__cancel = False

        self.__executed_suites = []
        self.__active_suites = []

    def __monitoring_enabled(self):

        return self.__kwargs.get("monitor_resources", False)

    def __create_xml_report(self):

        def __update_tag_stats(tag, status):

            tag.set("tests", str(int(suite.get("tests")) + 1))
            if status == TestCategory.SUCCESS:
                tag.set("passed", str(int(tag.get("passed")) + 1))
            else:
                tag.set("failures", str(int(tag.get("failures")) + 1))
            return tag

        if self.__kwargs.get("xml_report", None) is not None:
            write_file = self.__kwargs.get("xml_report")
            import os
            from xml.etree.ElementTree import ElementTree, Element, SubElement
            import xml
            if not os.path.exists(write_file):
                request = Element("root")
                ElementTree(request).write(write_file)

            xml_file = xml.etree.ElementTree.parse(write_file)
            root = xml_file.getroot()

            suites = self.get_executed_suites()

            for suite_object in suites:

                test_suite = suite_object.get_class_name()
                tests = suite_object.get_test_objects()

                for test_object in tests:

                    test_name = test_object.get_function_name()
                    test_metrics = test_object.metrics.get_metrics()

                    for class_param, class_param_data in test_metrics.items():
                        for param, param_data in class_param_data.items():

                            test_status = param_data["status"]
                            if test_status != TestCategory.SUCCESS:
                                test_status = "failure"
                            suite_found = False

                            for suite in root.iter("testsuite"):
                                suite_found = suite.attrib["name"] == test_suite
                                if suite_found:
                                    __update_tag_stats(suite, test_status)
                                    test = Element("testcase", name=str(test_name), status=str(test_status))
                                    if test_status == "failure":
                                        failure = Element("failure", type="failure")
                                        test.append(failure)
                                    suite.append(test)
                                    ElementTree(root).write(write_file)
                                    break

                            if not suite_found:
                                suite = SubElement(root, "testsuite", name=test_suite,
                                                   tests="0", passed="0", failures="0")
                                __update_tag_stats(suite, test_status)
                                test = SubElement(suite, "testcase", name=str(test_name), status=str(test_status))
                                if test_status == "failure":
                                    SubElement(test, "failure", type="failure")
                                ElementTree(root).write(write_file)

    def __create_html_report(self, reporter):

        if self.__kwargs.get("html_report", None) is not None:
            reporter.generate_html_report(self.__kwargs.get("html_report"))

    @staticmethod
    def __process_owners(suite_object):

        tests = suite_object.get_test_objects()
        for test in tests:
            if test.get_owner() is None:
                test.get_kwargs().update({"owner": suite_object.get_owner()})

    @staticmethod
    def __prioritize(suites=None, suite_object=None):
        """
        This function will order the lists of suites and tests according to the priority set by user
        - Suites/Tests with priorities, will be pushed towards the front according to the priorities defined
        - Suites/Tests with no priority defined, will be pushed towards the middle
        - Suites/Tests with no priority defined and not parallelized, will be pushed towards the end
        :param suites: LIST of class objects decorated with @Suite
        :param suite_object: SuiteObject
        :return: LIST ordered list of suites or tests
        """
        ordered = []
        priorities = {}
        no_priority = []
        not_parallelized = []

        items = suites if suites is not None else suite_object.get_test_objects()

        for item in items:

            if suites is not None:
                suite_object = Builder.get_execution_roster().get(item, None)
                priority = suite_object.get_priority()
                is_parallelized = suite_object.is_parallelized()
            else:
                priority = item.get_priority()
                is_parallelized = item.is_parallelized()
            if priority is None:
                if is_parallelized:
                    no_priority.append(item)
                else:
                    not_parallelized.append(item)
            else:
                if priority not in priorities:
                    priorities.update({priority: [item]})
                else:
                    priorities[priority].append(item)

        ordered_priorities = list(priorities.keys())
        ordered_priorities.sort()
        for priority in ordered_priorities:
            for item in priorities[priority]:
                ordered.append(item)

        ordered += no_priority + not_parallelized
        return ordered

    def get_executed_suites(self):
        """
        :return: LIST of SuiteObjects that begun executing
        """
        return self.__executed_suites

    def cancel(self):
        """
        Flips the switch to cancel the execution of tests
        :return: None
        """
        self.__cancel = True

    def run(self, **kwargs):
        """
        Initiates the execution process that runs tests
        :return: None
        """
        initial_start_time = time.time()
        resource_monitor = None
        try:
            if self.__monitoring_enabled():
                resource_monitor = ResourceMonitor()
                resource_monitor.start()
            self.__run_config = kwargs
            self.__processor = ParallelProcessor(**kwargs)

            parallels = []
            while self.__suites:
                for suite in list(self.__suites):
                    suite_object = Builder.get_execution_roster().get(suite, None)
                    if suite_object is not None:
                        if self.__processor.suite_multithreading() and suite_object.is_parallelized():
                            while True:
                                if self.__processor.suite_qualifies(suite_object):
                                    self.__executed_suites.append(suite_object)
                                    parallels.append(ParallelProcessor
                                                     .run_suite_in_a_thread(self.__run_suite, suite_object))
                                    self.__suites.remove(suite)
                                    break
                                elif suite_object.get_priority() is None:
                                    break
                                else:
                                    time.sleep(1)
                        else:
                            if not suite_object.is_parallelized():
                                LogJunkie.debug("Cant run suite: {} in parallel with any other suites. Waiting for "
                                                "parallel suites to finish so I can run it by itself."
                                                .format(suite_object.get_class_object()))
                                ParallelProcessor.wait_for_parallels_to_finish(parallels)
                            self.__executed_suites.append(suite_object)
                            self.__run_suite(suite_object)
                            self.__suites.remove(suite)
                    else:
                        LogJunkie.warn("Suite: {} not found! Make sure that your input is correct. "
                                       "If it is, make sure the use of Test Junkie's decorators "
                                       "is correct.".format(suite))
                        self.__suites.remove(suite)
                LogJunkie.debug("{} Suite(s) left in queue.".format(len(self.__suites)))
                time.sleep(1)

            for parallel in parallels:
                parallel.join()
        finally:
            if self.__monitoring_enabled():
                resource_monitor.shutdown()

        runtime = time.time() - initial_start_time
        print("----- done in {} seconds -----".format(runtime))
        aggregator = Aggregator(self.get_executed_suites())
        report = aggregator.get_basic_report()
        print("-- {} total tests".format(report["total"]))
        print("-- {} successful".format(report[TestCategory.SUCCESS]))
        print("-- {} failed".format(report[TestCategory.FAIL]))
        print("-- {} errors".format(report[TestCategory.ERROR]))
        print("-- {} ignored".format(report[TestCategory.IGNORE]))
        print("-- {} skipped".format(report[TestCategory.SKIP]))
        print("-- {} canceled".format(report[TestCategory.CANCEL]))
        if self.__kwargs.get("html_report", False):
            reporter = Reporter(monitoring_file=resource_monitor.get_file_path()
                                if resource_monitor is not None else None,
                                runtime=runtime,
                                aggregator=aggregator)
            self.__create_html_report(reporter)
        self.__create_xml_report()
        return aggregator

    @staticmethod
    def __validate_parameters(suite_object):
        """
        Validates the inputs for the parameter properties of tests and suites
        If parameters were passed in as an un-used function both to @Suites & to @tests,
        those functions will be executed when this function is called
        :param suite_object: test_junkie.objects.SuiteObject
        :return: None
        """
        def __validate(_parameters, _suite, _test=None):
            if not _parameters or not isinstance(_parameters, list):  # Validating parameters
                # If parameters are invalid, will raise a meaningful exception
                if isinstance(_parameters, list):
                    raise Exception("Empty parameters list in Class: {} {}"
                                    .format(_suite.get_class_module(),
                                            "Test: {}()".format(_test.get_function_name())
                                            if _test is not None else ""))
                else:
                    raise Exception("Wrong data type used for parameters. Expected: {}. Found: {} in "
                                    "Class: {} {}".format(list, type(_parameters),
                                                          _suite.get_class_module(),
                                                          " Test: {}()".format(_test.get_function_name())
                                                          if _test is not None else ""))

        __validate(suite_object.get_parameters(process_functions=True), suite_object)
        for test in suite_object.get_test_objects():
            __validate(test.get_parameters(process_functions=True), suite_object, test)

    def __run_suite(self, suite):
        suite_start_time = time.time()
        unsuccessful_tests = None
        self.__validate_parameters(suite)
        if not suite.can_skip(self.__run_config.get("features", None)) and not self.__cancel:
            Runner.__process_event(Event.ON_CLASS_IN_PROGRESS, suite=suite)
            for suite_retry_attempt in range(1, suite.get_retry_limit() + 1):
                if suite_retry_attempt == 1 or suite.get_status() in SuiteCategory.ALL_UN_SUCCESSFUL:

                    for class_param in suite.get_parameters(process_functions=True):

                        LogJunkie.debug("Running suite: {}".format(suite.get_class_object()))
                        LogJunkie.debug("Suite Retry {}/{} with Param: {}"
                                        .format(suite_retry_attempt, suite.get_retry_limit(), class_param))

                        before_class_error = Runner.__run_before_class(suite, class_param)

                        if suite_retry_attempt > 1:
                            unsuccessful_tests = suite.get_unsuccessful_tests()
                            LogJunkie.debug("There are {} unsuccessful tests that need to be retried"
                                            .format(len(unsuccessful_tests)))
                            if not unsuccessful_tests:
                                break
                        parallels = []

                        tests = list(suite.get_test_objects())
                        while tests:
                            for test in list(tests):
                                if not test.is_parallelized():
                                    LogJunkie.debug("Cant run test: {} in parallel with any other tests"
                                                    .format(test.get_function_object()))
                                    ParallelProcessor.wait_for_parallels_to_finish(parallels)
                                while self.__processor.test_limit_reached(parallels):
                                    time.sleep(1)
                                test_start_time = time.time()  # will use in case of a failure in context of this loop

                                if not Runner.__positive_skip_condition(test=test, run_config=self.__run_config) and \
                                        Runner.__runnable_tags(test=test, run_config=self.__run_config):

                                    for param in test.get_parameters(process_functions=True):
                                        if unsuccessful_tests is not None:
                                            if not test.is_qualified_for_retry(param, class_param=class_param):
                                                # If does not qualify with current parameter, will move to the next
                                                continue
                                        if ((self.__processor.test_multithreading()
                                             and param is None) or (self.__processor.test_multithreading()
                                                                    and test.parallelized_parameters()
                                                                    and param is not None)):
                                            while True:
                                                if self.__processor.test_qualifies(suite, test):
                                                    parallels.append(
                                                        self.__processor.run_test_in_a_thread(Runner.__run_test,
                                                                                              suite, test, param,
                                                                                              class_param,
                                                                                              before_class_error,
                                                                                              self.__cancel))
                                                    break
                                                elif test.get_priority() is None:
                                                    break
                                                else:
                                                    time.sleep(1)
                                        else:
                                            Runner.__run_test(suite=suite, test=test,
                                                              parameter=param,
                                                              class_parameter=class_param,
                                                              before_class_error=before_class_error,
                                                              cancel=self.__cancel)
                                    tests.remove(test)

                                else:
                                    tests.remove(test)
                                    test.metrics.update_metrics(status=TestCategory.SKIP, start_time=test_start_time)
                                    Runner.__process_event(Event.ON_SKIP, suite=suite, test=test, class_param=class_param)

                        ParallelProcessor.wait_for_parallels_to_finish(parallels)
                        Runner.__run_after_class(suite, class_param)
                    suite.metrics.update_suite_metrics(status=SuiteCategory.FAIL
                                                       if suite.has_unsuccessful_tests() else SuiteCategory.SUCCESS,
                                                       start_time=suite_start_time)
            Runner.__process_event(Event.ON_CLASS_COMPLETE, suite=suite)
        elif self.__cancel:
            suite.metrics.update_suite_metrics(status=SuiteCategory.CANCEL, start_time=suite_start_time)
            Runner.__process_event(Event.ON_CLASS_CANCEL, suite=suite)
        else:
            suite.metrics.update_suite_metrics(status=SuiteCategory.SKIP, start_time=suite_start_time)
            Runner.__process_event(Event.ON_CLASS_SKIP, suite=suite)

    @staticmethod
    def __run_test(suite, test, parameter=None, class_parameter=None, before_class_error=None, cancel=False):
        test_start_time = time.time()
        if before_class_error is not None or cancel:
            _status = TestCategory.IGNORE if not cancel else TestCategory.CANCEL
            _event = Event.ON_IGNORE if not cancel else Event.ON_CANCEL
            test.metrics.update_metrics(status=_status,
                                        start_time=test_start_time,
                                        param=parameter,
                                        class_param=class_parameter,
                                        exception=before_class_error)
            Runner.__process_event(_event, error=before_class_error, suite=suite, test=test,
                                   class_param=class_parameter, param=parameter)
            return

        if not test.accepts_suite_parameters():
            # for reporting purposes, so reports are properly nested
            class_parameter = None

        status = test.get_status(parameter, class_parameter)
        if not test.accepts_suite_parameters() and status is not None:
            """
            making sure that we do not run tests with suite parameters if suite parameters are not accepted in the
            test signature. But we still want to run all other parameters and tests without any params.
            Also we want to make sure we honor the suite level retries
            """
            if status != TestCategory.SUCCESS:  # test already ran and was unsuccessful
                # if it did not reach its max retry limit, will rerun it again
                max_retry_allowed = suite.get_retry_limit() * test.get_retry_limit()
                actual_retries = test.get_number_of_actual_retries(parameter, class_parameter)
                if actual_retries >= max_retry_allowed:
                    return
            else:
                return

        for retry_attempt in range(1, test.get_retry_limit() + 1):
            if test.is_qualified_for_retry(parameter, class_param=class_parameter):
                LogJunkie.debug("\n===============Running test==================\n"
                                "Test Case: {}\n"
                                "Test Suite: {}\n"
                                "Test Parameter: {}\n"
                                "Class Parameter: {}\n"
                                "Retry Attempt: {}/{}\n"
                                "============================================="
                                .format(test.get_function_name(), suite.get_class_name(), parameter, class_parameter,
                                        retry_attempt, test.get_retry_limit()))
                try:
                    if not test.accepts_test_parameters() and parameter is not None:
                        raise Exception("parameters=[...] property was used on: {}.{} but parameter is not "
                                        "accepted as part of the function's signature"
                                        .format(test.get_function_module(), test.get_function_name()))
                    suite.get_rules().before_test()
                    Runner.__process_decorator(decorator_type=DecoratorType.BEFORE_TEST, suite=suite,
                                               class_parameter=class_parameter)
                    Runner.__process_decorator(decorator_type=DecoratorType.TEST_CASE, suite=suite,
                                               test=test, parameter=parameter, class_parameter=class_parameter)
                    Runner.__process_decorator(decorator_type=DecoratorType.AFTER_TEST, suite=suite,
                                               class_parameter=class_parameter)
                    suite.get_rules().after_test()
                    Runner.__process_event(Event.ON_SUCCESS, suite=suite, test=test,
                                           class_param=class_parameter, param=parameter)
                    return
                except Exception as error:

                    if not isinstance(error, TestJunkieExecutionError):
                        traceback.print_exc()
                        __category = TestCategory.ERROR
                        __event = Event.ON_ERROR
                        if isinstance(error, AssertionError):
                            __category = TestCategory.FAIL
                            __event = Event.ON_FAILURE
                        test.metrics.update_metrics(status=__category,
                                                    start_time=test_start_time,
                                                    param=parameter,
                                                    class_param=class_parameter,
                                                    exception=error)
                        Runner.__process_event(__event, suite=suite, test=test, error=error,
                                               class_param=class_parameter, param=parameter)
                    else:
                        raise error

    @staticmethod
    def __run_before_class(suite, class_parameter=None):
        before_class_error = None
        try:
            suite.get_rules().before_class()
            Runner.__process_decorator(decorator_type=DecoratorType.BEFORE_CLASS, suite=suite,
                                       class_parameter=class_parameter)
        except Exception as error:
            if isinstance(error, AssertionError):
                Runner.__process_event(Event.ON_BEFORE_CLASS_FAIL, suite=suite, error=error,
                                       class_param=class_parameter)
            else:
                Runner.__process_event(Event.ON_BEFORE_CLASS_ERROR, suite=suite, error=error,
                                       class_param=class_parameter)
            before_class_error = error
        return before_class_error

    @staticmethod
    def __run_after_class(suite, class_parameter=None):
        try:
            Runner.__process_decorator(decorator_type=DecoratorType.AFTER_CLASS, suite=suite,
                                       class_parameter=class_parameter)
            suite.get_rules().after_class()
        except Exception as error:
            if isinstance(error, AssertionError):
                Runner.__process_event(Event.ON_AFTER_CLASS_FAIL, suite=suite, error=error,
                                       class_param=class_parameter)
            else:
                Runner.__process_event(Event.ON_AFTER_CLASS_ERROR, suite=suite, error=error,
                                       class_param=class_parameter)

    @staticmethod
    def __process_decorator(decorator_type, suite, test=None, parameter=None,  class_parameter=None):
        start_time = time.time()
        if DecoratorType.TEST_CASE != decorator_type:
            functions_list = suite.get_decorated_definition(decorator_type)
            for func in functions_list:
                try:
                    # deprecated but supports Python 2
                    if "suite_parameter" in inspect.getargspec(func["decorated_function"]).args:
                        func["decorated_function"](suite.get_class_object()(), suite_parameter=class_parameter)
                    else:
                        func["decorated_function"](suite.get_class_object()())
                    suite.metrics.update_decorator_metrics(decorator_type, start_time)
                except Exception as error:
                    suite.metrics.update_decorator_metrics(decorator_type, start_time, error)
                    raise error
        else:
            if test.accepts_test_and_suite_parameters():
                test.get_function_object()(suite.get_class_object()(),
                                           parameter=parameter, suite_parameter=class_parameter)
            elif test.accepts_suite_parameters():
                test.get_function_object()(suite.get_class_object()(), suite_parameter=class_parameter)
            elif test.accepts_test_parameters():
                test.get_function_object()(suite.get_class_object()(), parameter=parameter)
            else:
                test.get_function_object()(suite.get_class_object()())
            test.metrics.update_metrics(status=TestCategory.SUCCESS, start_time=start_time,
                                        param=parameter, class_param=class_parameter)

    @staticmethod
    def __process_event(event, suite, test=None, param=None, class_param=None, error=None):

        event_mapping = {Event.ON_SUCCESS: {"custom": suite.get_listener().on_success,
                                            "native": Listener().on_success},
                         Event.ON_FAILURE: {"custom": suite.get_listener().on_failure,
                                            "native": Listener().on_failure},
                         Event.ON_ERROR: {"custom": suite.get_listener().on_error,
                                          "native": Listener().on_error},
                         Event.ON_SKIP: {"custom": suite.get_listener().on_skip,
                                         "native": Listener().on_skip},
                         Event.ON_CANCEL: {"custom": suite.get_listener().on_cancel,
                                           "native": Listener().on_cancel},
                         Event.ON_IGNORE: {"custom": suite.get_listener().on_ignore,
                                           "native": Listener().on_ignore},
                         Event.ON_CLASS_CANCEL: {"custom": suite.get_listener().on_class_cancel,
                                                 "native": Listener().on_class_cancel},
                         Event.ON_CLASS_SKIP: {"custom": suite.get_listener().on_class_skip,
                                               "native": Listener().on_class_skip},
                         Event.ON_BEFORE_CLASS_ERROR: {"custom": suite.get_listener().on_before_class_error,
                                                       "native": Listener().on_before_class_error},
                         Event.ON_BEFORE_CLASS_FAIL: {"custom": suite.get_listener().on_before_class_failure,
                                                      "native": Listener().on_before_class_failure},
                         Event.ON_AFTER_CLASS_ERROR: {"custom": suite.get_listener().on_after_class_error,
                                                      "native": Listener().on_after_class_error},
                         Event.ON_AFTER_CLASS_FAIL: {"custom": suite.get_listener().on_after_class_failure,
                                                     "native": Listener().on_after_class_failure},
                         Event.ON_CLASS_IN_PROGRESS: {"custom": suite.get_listener().on_class_in_progress,
                                                      "native": Listener().on_class_in_progress},
                         Event.ON_CLASS_COMPLETE: {"custom": suite.get_listener().on_class_complete,
                                                   "native": Listener().on_class_complete}
                         }

        native_function = event_mapping[event]["native"]
        custom_function = event_mapping[event]["custom"]
        custom_function = custom_function if str(custom_function).split(" at ")[0] != \
                                             str(native_function).split(" at ")[0] else None

        @synchronized(threading.Lock())
        def __create_properties():
            properties = {"suite_meta": suite.get_meta(),
                          "test_meta": test.get_meta(param, class_param) if test else None,
                          "jm": {}}
            if test:
                properties["test_meta"].update({"parameter": param})
                properties["jm"].update({"jto": test, "jso": suite})
            properties["suite_meta"].update({"parameter": class_param})
            return copy.deepcopy(properties)
        try:

            if error is not None:
                native_function(custom_function=custom_function,
                                properties=__create_properties(),
                                error=error)
            else:
                native_function(custom_function=custom_function,
                                properties=__create_properties())
        except Exception:
            traceback.print_exc()
            raise TestListenerError("Exception occurred while processing custom event listener with: {}"
                                    .format(custom_function))

    @staticmethod
    def __runnable_tags(test, run_config):
        """
        This function evaluates if test should be executed based on its tags and the tag config
        :param test: TestObject
        :param run_config: DICT
        :return: BOOLEAN
        """
        test_tags = test.get_tags()
        tag_config = run_config.get("tag_config", {})

        def __config_set(config):
            return tag_config.get(config, None) is not None

        def __full_match(config):
            for tag in tag_config[config]:
                if tag not in test_tags:
                    return False
            return True

        def __partial_match(config):
            for tag in tag_config[config]:
                if tag in test_tags:
                    return True

        if tag_config is not None:
            try:
                if __config_set("skip_on_match_all") and __full_match("skip_on_match_all"):
                    return False
                elif __config_set("skip_on_match_any") and __partial_match("skip_on_match_any"):
                    return False
                elif __config_set("run_on_match_all") and __full_match("run_on_match_all"):
                    return True
                elif __config_set("run_on_match_any") and __partial_match("run_on_match_any"):
                    return True
            except Exception:
                traceback.print_exc()
                raise ConfigError("Error occurred while trying to parse `tag_config`")
        return True

    @staticmethod
    def __positive_skip_condition(test, run_config):
        """
        This function will evaluate inputs for skip parameter whether its a function or a boolean
        :param test: TestObject object
        :param run_config: DICT
        :return: BOOLEAN
        """
        val = test.can_skip()
        components = run_config.get("components", None)
        if val is False and components is not None:
            val = not test.get_component() in components
        return val
