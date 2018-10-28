import copy
import inspect
import threading
import time

from test_junkie.constants import SuiteCategory, TestCategory
from test_junkie.debugger import LogJunkie
from test_junkie.decorators import DecoratorType, synchronized
from test_junkie.errors import ConfigError, TestJunkieExecutionError, TestListenerError
from test_junkie.parallels import ParallelProcessor


class Runner:

    __STATS = {}

    def __init__(self, suites, **kwargs):

        self.__stats = {}

        self.__suites = suites
        if not isinstance(self.__suites, list):
            self.__suites = [self.__suites]
        self.__kwargs = kwargs

        self.__processor = None
        self.__run_config = {}

        self.__cancel = False

        self.__executed_suites = []
        self.__active_suites = []

    def get_executed_suites(self):

        return self.__executed_suites

    def cancel(self):

        self.__cancel = True

    def run(self, **kwargs):
        """
        This function initiates the testing process
        :return: None
        """
        initial_start_time = time.time()
        from test_junkie.builder import Builder

        self.__run_config = kwargs
        self.__processor = ParallelProcessor(**kwargs)

        parallels = []
        while self.__suites:
            for suite in self.__suites:  # TODO wait due to remove call which changes list size?
                suite_object = Builder.get_execution_roster().get(suite, None)
                if suite_object is not None:
                    if not suite_object.is_parallelized():
                        LogJunkie.debug("Cant run suite: {} in parallel with any other suites"
                                        .format(suite_object.get_class_object()))
                        ParallelProcessor.wait_for_parallels_to_finish(parallels)
                    if self.__processor.suite_multithreading():
                        if self.__processor.suite_qualifies(suite_object):
                            self.__executed_suites.append(suite_object)
                            parallels.append(ParallelProcessor.run_suite_in_a_thread(self.__run_suite, suite_object))
                            self.__suites.remove(suite)
                    else:
                        self.__executed_suites.append(suite_object)
                        self.__run_suite(suite_object)
                        self.__suites.remove(suite)
                else:
                    LogJunkie.debug("Suite: {} not found!".format(suite))
                    self.__suites.remove(suite)
            LogJunkie.debug("{} Suite(s) left in queue.".format(len(self.__suites)))
            time.sleep(1)

        for parallel in parallels:
            parallel.join()

        print("--- done in {} seconds ---".format(time.time() - initial_start_time))

    def __run_suite(self, suite):
        suite_start_time = time.time()
        unsuccessful_tests = None
        if not suite.can_skip() and not self.__cancel:
            for suite_retry_attempt in range(1, suite.get_retry_limit() + 1):
                if suite_retry_attempt == 1 or suite.get_status() in SuiteCategory.ALL_UN_SUCCESSFUL:
                    # TODO add param validation, reuse the existing function with slight modifications
                    for class_param in suite.get_parameters():

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

                        for test in suite.get_test_objects():
                            if not test.is_parallelized():
                                LogJunkie.debug("Cant run test: {} in parallel with any other tests"
                                                .format(test.get_function_object()))
                                ParallelProcessor.wait_for_parallels_to_finish(parallels)
                            while self.__processor.test_limit_reached(parallels):
                                time.sleep(1)
                            test_start_time = time.time()  # will be used in case of a failure in context of this loop

                            LogJunkie.debug("===============Running test: {}=================="
                                            .format(test.get_function_object()))

                            if not Runner.__positive_skip_condition(test) and \
                                    Runner.__runnable_tags(test=test,
                                                           tag_config=self.__run_config.get("tag_config", {})):
                                parameters = test.get_parameters()
                                if not parameters or not isinstance(parameters, list):  # Validating parameters
                                    # If parameters are invalid, will raise a meaningful exception
                                    try:
                                        if isinstance(parameters, list):
                                            raise Exception("Empty parameters list in Class: {} Function: {}"
                                                            .format(suite.get_class_module(), test.get_function_name()))
                                        else:
                                            raise Exception("Wrong parameters data type. Expected: {} was: {} in "
                                                            "Class: {} Function: {}".format(list, type(parameters),
                                                                                            suite.get_class_module(),
                                                                                            test.get_function_name()))
                                    except Exception as error:
                                        LogJunkie.print_traceback()
                                        test.metrics.update_metrics(status=TestCategory.IGNORE,
                                                                    start_time=test_start_time,
                                                                    exception=error)
                                        Runner.__process_event_listener(suite.get_listener().on_ignore,
                                                                        suite=suite, error=error,
                                                                        class_param=class_param)
                                else:  # If parameters are valid, will continue processing the test
                                    for param in parameters:
                                        if unsuccessful_tests is not None:
                                            if not test._is_qualified_for_retry(param, class_param=class_param):
                                                # If test does not qualify with current parameter, will move to the next
                                                continue
                                        if self.__processor.test_multithreading() and test.parallelized_parameters():
                                            while self.__processor.test_limit_reached(parallels):
                                                time.sleep(1)
                                            parallels.append(self.__processor.run_test_in_a_thread(
                                                Runner.__run_test, suite, test, param, class_param,
                                                before_class_error, self.__cancel))
                                        else:
                                            Runner.__run_test(suite=suite, test=test,
                                                              parameter=param,
                                                              class_parameter=class_param,
                                                              before_class_error=before_class_error,
                                                              cancel=self.__cancel)
                            else:
                                test.metrics.update_metrics(status=TestCategory.SKIP, start_time=test_start_time)
                                Runner.__process_event_listener(suite.get_listener().on_skip, suite=suite, test=test,
                                                                class_param=class_param)

                        ParallelProcessor.wait_for_parallels_to_finish(parallels)
                        Runner.__run_after_class(suite, class_param)
                    suite.metrics.update_suite_metrics(status=SuiteCategory.FAIL
                                                       if suite.has_unsuccessful_tests() else SuiteCategory.SUCCESS,
                                                       start_time=suite_start_time)
        elif self.__cancel:
            suite.metrics.update_suite_metrics(status=SuiteCategory.CANCEL, start_time=suite_start_time)
            Runner.__process_event_listener(suite.get_listener().on_class_cancel, suite=suite)
        else:
            suite.metrics.update_suite_metrics(status=SuiteCategory.SKIP, start_time=suite_start_time)
            Runner.__process_event_listener(suite.get_listener().on_class_skip, suite=suite)

    @staticmethod
    def __run_test(suite, test, parameter=None, class_parameter=None, before_class_error=None, cancel=False):

        test_start_time = time.time()
        if before_class_error is not None or cancel:
            _status = TestCategory.IGNORE if not cancel else TestCategory.CANCEL
            _event = suite.get_listener().on_ignore if not cancel else suite.get_listener().on_cancel
            test.metrics.update_metrics(status=_status,
                                        start_time=test_start_time,
                                        param=parameter,
                                        class_param=class_parameter,
                                        exception=before_class_error)
            Runner.__process_event_listener(_event, error=before_class_error, suite=suite, test=test,
                                            class_param=class_parameter, param=parameter)
            return

        for retry_attempt in range(1, test.get_retry_limit() + 1):
            LogJunkie.debug(">> Test Case: {} Param: {} Retry Attempt: {}/{}"
                            .format(test.get_function_object(), parameter, retry_attempt, test.get_retry_limit()))
            try:
                suite.get_rules().before_test()
                Runner.__process_decorator(decorator_type=DecoratorType.BEFORE_TEST, suite=suite,
                                           class_parameter=class_parameter)
                Runner.__process_decorator(decorator_type=DecoratorType.TEST_CASE, suite=suite,
                                           test=test, parameter=parameter, class_parameter=class_parameter)
                Runner.__process_decorator(decorator_type=DecoratorType.AFTER_TEST, suite=suite,
                                           class_parameter=class_parameter)
                suite.get_rules().after_test()
                Runner.__process_event_listener(suite.get_listener().on_success, suite=suite, test=test,
                                                class_param=class_parameter, param=parameter)
                return
            except Exception as error:

                if not isinstance(error, TestJunkieExecutionError):
                    LogJunkie.print_traceback()
                    __category = TestCategory.ERROR
                    __event = suite.get_listener().on_error
                    if isinstance(error, AssertionError):
                        __category = TestCategory.FAIL
                        __event = suite.get_listener().on_failure
                    test.metrics.update_metrics(status=__category,
                                                start_time=test_start_time,
                                                param=parameter,
                                                class_param=class_parameter,
                                                exception=error)
                    Runner.__process_event_listener(__event, suite=suite, test=test, error=error,
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
                Runner.__process_event_listener(suite.get_listener().on_before_class_failure, suite=suite, error=error,
                                                class_param=class_parameter)
            else:
                Runner.__process_event_listener(suite.get_listener().on_before_class_error, suite=suite, error=error,
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
                Runner.__process_event_listener(suite.get_listener().on_after_class_failure, suite=suite, error=error,
                                                class_param=class_parameter)
            else:
                Runner.__process_event_listener(suite.get_listener().on_after_class_error, suite=suite, error=error,
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
    def __process_event_listener(event_function, suite, test=None, param=None, class_param=None, error=None):

        @synchronized(threading.Lock())
        def __create_properties():
            properties = {"suite_meta": suite.get_meta(),
                          "test_meta": test.get_meta(param, class_param) if test else None,
                          "junkie_meta": {}}
            if test:
                properties["test_meta"].update({"parameter": param})
            properties["suite_meta"].update({"parameter": class_param})
            return copy.deepcopy(properties)
        try:

            if error is not None:
                event_function(__create_properties(), error)
            else:
                event_function(__create_properties())
        except Exception:
            LogJunkie.print_traceback()
            raise TestListenerError("Exception occurred while processing custom event listener with: {}"
                                    .format(event_function))

    @staticmethod
    def __runnable_tags(test, tag_config):
        """
        This function evaluates if test should be executed based on its tags and the tag config
        :param test: TestObject
        :param tag_config: DICT tag configuration
        :return: BOOLEAN
        """
        test_tags = test.get_tags()

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
                LogJunkie.print_traceback()
                raise ConfigError("Error occurred while trying to parse `tag_config`")
        return True

    @staticmethod
    def __positive_skip_condition(test):
        """
        This function will evaluate inputs for skip parameter whether its a function or a boolean
        :param suite: SuiteObject object
        :param test: TestObject object
        :return: BOOLEAN
        """
        val = test.can_skip()
        if inspect.isfunction(val):
            try:
                if "meta" in inspect.getargspec(val).args:  # deprecated but supports Python 2
                    val = val(meta=test.get_meta())
                else:
                    val = val()
                assert isinstance(val, bool), "Function: {} must return a boolean. Got: {}".format(val, type(val))
            except Exception:
                LogJunkie.print_traceback()
                raise TestJunkieExecutionError("Encountered error while processing skip condition")
        return val
