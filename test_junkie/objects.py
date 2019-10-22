import copy
import inspect
import traceback
import sys
from test_junkie.decorators import DecoratorType
from test_junkie.constants import TestCategory
from test_junkie.errors import TestJunkieExecutionError, BadParameters
from test_junkie.metrics import ClassMetrics, TestMetrics, Aggregator


class _FuncEval:

    @staticmethod
    def eval_skip(obj):

        val = obj.get_skip()
        try:
            if not isinstance(val, bool):
                if inspect.isfunction(val):
                    val = val(meta=obj.get_meta()) if "meta" in inspect.getargspec(val).args else val()
                elif inspect.ismethod(val):
                    val = getattr(val.__self__, val.__name__)(meta=obj.get_meta()) \
                        if "meta" in inspect.getargspec(val).args \
                        else getattr(val.__self__, val.__name__)()
                else:
                    raise BadParameters("Unsupported data type used to pass parameters to the skip property in test: "
                                        "{}.{}".format(obj.get_function_module(), obj.get_function_name()))
                assert isinstance(val, bool), "You were using a function/unbound method to pass parameters to the skip"\
                                              " property in test {}.{} which must return a boolean value. "\
                                              "Got: {} instead of a boolean".format(obj.get_function_module(),
                                                                                    obj.get_function_name(), type(val))
        except Exception:
            traceback.print_exc()
            raise TestJunkieExecutionError("Encountered error while processing skip condition")
        return val

    @staticmethod
    def eval_params(params):

        try:
            if inspect.isfunction(params):
                return params()
            elif inspect.ismethod(params):
                return getattr(params.__self__, params.__name__)()
        except Exception:
            traceback.print_exc()
            raise TestJunkieExecutionError("Encountered error while processing parameters "
                                           "passed in via function or unbound method: {}".format(params))
        return params


class SuiteObject(object):

    def __init__(self, suite_definition):

        self.__suite_definition = suite_definition
        self.__listener = suite_definition["test_listener"](class_meta=suite_definition["class_meta"])
        self.__tests = []
        self.__test_function_names = []  # this suite has tests with those function names
        self.__test_components = []  # this suite has tests that address those components
        self.__test_tags = []  # this suite has tests that are tagged with those tags
        self.__test_function_objects = []
        for test in suite_definition["suite_definition"].get(DecoratorType.TEST_CASE):
            test_obj = TestObject(test)
            self.__tests.append(test_obj)
            self.__test_function_names.append(test_obj.get_function_name())
            self.__test_function_objects.append(test_obj.get_function_object())
            self.__test_components.append(test_obj.get_component())
            self.__test_tags += test_obj.get_tags()
        self.__test_tags, self.__test_function_objects = set(self.__test_tags), set(self.__test_function_objects)
        self.metrics = ClassMetrics()
        self.__rules = suite_definition["test_rules"](suite=copy.deepcopy(self))
        self.__instance = None

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def get_suite_id(self):
        return self.get_kwargs().get("testjunkie_suite_id", 0)

    def get_decorated_definition(self, decorator_type):

        return self.__suite_definition["suite_definition"].get(decorator_type)

    def get_test_count(self):

        return len(self.__tests)

    def get_class_name(self):

        return self.__suite_definition["class_name"]

    def get_class_instance(self):

        if self.__instance is None:
            self.__instance = self.__suite_definition["class_object"]()
        return self.__instance

    def get_class_object(self):

        return self.__suite_definition["class_object"]

    def get_class_module(self):

        return self.get_class_object().__module__

    def _update_test_meta(self, parameter=None, suite_parameter=None, **kwargs):

        for frame in inspect.stack():
            try:
                getattr(self.get_class_object(), str(inspect.getframeinfo(frame[0]).function))
                test_function_name = str(inspect.getframeinfo(frame[0]).function)
                for test_object in self.get_test_objects():
                    if test_object.get_function_name() == test_function_name:
                        test_object.get_meta(parameter, suite_parameter).update(kwargs)
                        return True
                return False
            except:
                pass
        return False

    def _get_test_meta(self, parameter=None, suite_parameter=None):

        for frame in inspect.stack():
            try:
                getattr(self.get_class_object(), str(inspect.getframeinfo(frame[0]).function))
                test_function_name = str(inspect.getframeinfo(frame[0]).function)
                for test_object in self.get_test_objects():
                    if test_object.get_function_name() == test_function_name:
                        return test_object.get_meta(parameter, suite_parameter)
            except:
                pass

    def update_test_objects(self, tests):

        self.__tests = tests

    def get_test_objects(self):
        """
        Use to get all TJ TestObjects
        :return: LIST of TestObjects
        """
        return self.__tests

    def get_test_function_names(self):
        """
        Use to get actual names of the test functions
        :return: LIST of STRINGS
        """
        return self.__test_function_names

    def get_test_components(self):
        """
        Use to get all the components that are covered by tests in this suite
        :return: LIST of STRINGS
        """
        return self.__test_components

    def get_test_tags(self):
        """
        Use to get all the tags that are covered by tests in this suite
        :return: LIST of STRINGS
        """
        return self.__test_tags

    def get_test_function_objects(self):
        """
        Use to get actual function objects
        :return: LIST of STRINGS
        """
        return self.__test_function_objects

    def get_skip(self):
        return self.__suite_definition.get("class_skip", False)

    def can_skip(self, settings):
        """
        This function determines if the whole suite needs to be skipped.
        - if user asked to run tests for specific feature, it will check to make sure this suite matches that feature
        - if user asked to run tests for specific container, it will check to make sure suite has related tests
        - if user asked to run specific tags, it will verify that suite has tests with those tags
        - If user asked to run specific tests, it will check to make sure suite has that test
        :param settings: Settings object
        :return: If suite qualifies, it will return False, other wise it will return True.
        """
        def __all_tags_match(expected, actual):

            for _tag in expected:
                if _tag not in actual:
                    return False
            return True

        can_skip = _FuncEval.eval_skip(self)

        if settings.features is not None and can_skip is False:
            can_skip = not self.get_feature() in settings.features

        if settings.components is not None and can_skip is False:
            for component in settings.components:
                if component not in self.get_test_components():
                    return True

        if settings.tags is not None and can_skip is False:

            if settings.tags.get("run_on_match_any", None) is not None:
                for tag in settings.tags["run_on_match_any"]:
                    if tag in self.get_test_tags():
                        return False
                return True

            if settings.tags.get("run_on_match_all", None) is not None:
                for test_obj in self.get_test_objects():
                    if __all_tags_match(expected=settings.tags["run_on_match_all"], actual=test_obj.get_tags()):
                        return False
                return True

        if settings.tests is not None and can_skip is False:
            for test in settings.tests:
                if inspect.ismethod(test) or inspect.isfunction(test):
                    test = test.__name__
                if test in self.get_test_function_names():
                    return False
            return True

        return can_skip

    def get_retry_limit(self):

        return self.__suite_definition.get("class_retry", 1)

    def get_rules(self):

        return self.__rules

    def get_listener(self):

        return self.__listener

    def get_meta(self, copy_of_meta=False):

        if copy_of_meta:
            return copy.deepcopy(self.__suite_definition.get("class_meta", {}))
        else:
            return self.__suite_definition.get("class_meta", {})

    def get_unsuccessful_tests(self):

        unsuccessful_tests = []
        tests = self.get_test_objects()
        for test in tests:
            for class_param, metrics in test.metrics.get_metrics().items():
                for value in metrics.values():
                    if value["status"] in TestCategory.ALL_UN_SUCCESSFUL:
                        unsuccessful_tests.append(test)
        unsuccessful_tests = list(set(unsuccessful_tests))
        return unsuccessful_tests

    def has_unsuccessful_tests(self):

        tests = self.get_test_objects()
        for test in tests:
            for class_param, metrics in test.metrics.get_metrics().items():
                for value in metrics.values():
                    if value["status"] in TestCategory.ALL_UN_SUCCESSFUL:
                        return True
        return False

    def get_status(self):

        return self.metrics.get_metrics()["status"]

    def get_owner(self):

        return self.get_kwargs().get("owner", None)

    def get_parallel_restrictions(self):

        return self.get_kwargs().get("pr", [])

    def get_parameters(self, process_functions=False):
        if process_functions:
            parameters = self.__suite_definition["class_parameters"]
            eval_result = _FuncEval.eval_params(parameters)
            if eval_result is not None:
                self.__suite_definition["class_parameters"] = eval_result
        return self.__suite_definition["class_parameters"]

    def get_kwargs(self):

        return self.__suite_definition["decorator_kwargs"]

    def is_parallelized(self):

        return self.__suite_definition["parallelized"]

    def get_feature(self):

        return self.get_kwargs().get("feature", None)

    def get_priority(self):

        return self.get_kwargs().get("priority", None)

    def __get_average_metric(self, decorator, metric):

        from statistics import mean
        performance = self.metrics.get_metrics().get(decorator, {}).get(metric, None)
        return mean(performance) if performance else None

    def get_average_performance_of_after_class(self):
        return self.__get_average_metric(DecoratorType.AFTER_CLASS, "performance")

    def get_average_performance_of_before_class(self):
        return self.__get_average_metric(DecoratorType.BEFORE_CLASS, "performance")

    def get_average_performance_of_after_test(self):
        return self.__get_average_metric(DecoratorType.AFTER_TEST, "performance")

    def get_average_performance_of_before_test(self):
        return self.__get_average_metric(DecoratorType.BEFORE_TEST, "performance")

    def get_runtime(self):

        return self.metrics.get_metrics().get("runtime", None)

    def get_number_of_actual_retries(self):

        return self.metrics.get_metrics().get("retries", None)

    def get_data_by_tags(self):

        data = {"_totals_": Aggregator.get_template()}
        for test in self.get_test_objects():
            test_metrics = test.metrics.get_metrics()
            if test.get_tags():
                for tag in test.get_tags():
                    if tag not in data:
                        data.update({tag: Aggregator.get_template()})
                    Aggregator._update_report(data, test_metrics, tag)
            else:
                if None not in data:
                    data.update({None: Aggregator.get_template()})
                Aggregator._update_report(data, test_metrics, None)
        return data


class TestObject(object):

    def __init__(self, test_definition):

        self.__test_definition = test_definition

        self.metrics = TestMetrics()

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def get_test_id(self):
        return self.get_kwargs().get("testjunkie_test_id", 0)

    def get_suite_id(self):
        return self.get_kwargs().get("testjunkie_suite_id", 0)

    def get_skip(self):
        return self.get_kwargs().get("skip", False)

    def can_skip(self):
        return _FuncEval.eval_skip(self)

    def skip_before_test_rule(self):
        return self.get_kwargs().get("skip_before_test_rule", False)

    def skip_before_test(self):
        return self.get_kwargs().get("skip_before_test", False)

    def skip_after_test_rule(self):
        return self.get_kwargs().get("skip_after_test_rule", False)

    def skip_after_test(self):
        return self.get_kwargs().get("skip_after_test", False)

    def get_owner(self):

        return self.get_kwargs().get("owner", None)

    def get_priority(self):

        return self.get_kwargs().get("priority", None)

    def get_parameters(self, process_functions=False):
        if process_functions:
            parameters = self.get_kwargs().get("parameters", [None])
            eval_result = _FuncEval.eval_params(parameters)
            if eval_result is not None:
                self.get_kwargs()["parameters"] = eval_result
        return self.get_kwargs().get("parameters", [None])

    def get_retry_limit(self):

        return self.get_kwargs().get("retry", 1)

    def get_function_name(self):

        return self.get_function_object().__name__

    def get_function_module(self):

        return self.get_function_object().__module__

    def get_function_object(self):

        return self.__test_definition["decorated_function"]

    def get_parallel_restrictions(self):

        return self.get_kwargs().get("pr", [])

    def get_tags(self):

        return self.get_kwargs().get("tags", [])

    def get_meta(self, parameter=None, class_parameter=None, copy_of_meta=False):

        string_param = str(parameter)
        string_class_param = str(class_parameter)

        if not self.get_kwargs().get("meta", {}):  # does not require meta to be defined in order to Meta.update it
            self.get_kwargs().update({"meta": {}})
        meta = self.get_kwargs()["meta"]

        if "original" not in meta:
            meta.update({"original": copy.deepcopy(meta)})

        if string_class_param not in meta:
            meta.update({string_class_param: {string_param: copy.deepcopy(meta["original"])}})

        if string_param not in meta[string_class_param]:
            meta[string_class_param].update({string_param: copy.deepcopy(meta["original"])})
        if copy_of_meta:
            return copy.deepcopy(meta[string_class_param][string_param])
        else:
            return meta[string_class_param][string_param]

    def get_kwargs(self):

        return self.__test_definition["decorator_kwargs"]

    def get_no_retry_on(self):

        return self.get_kwargs().get("no_retry_on", [])

    def get_retry_on(self):

        return self.get_kwargs().get("retry_on", [])

    def get_component(self):

        return self.get_kwargs().get("component", None)

    def is_parallelized(self):

        return self.get_kwargs().get("parallelized", True)

    def parallelized_parameters(self):

        return self.get_kwargs().get("parallelized_parameters", False)

    def accepts_test_and_suite_parameters(self):

        return "parameter" in inspect.getargspec(self.get_function_object()).args and \
               "suite_parameter" in inspect.getargspec(self.get_function_object()).args

    def accepts_test_parameters(self):

        return "parameter" in inspect.getargspec(self.get_function_object()).args

    def accepts_suite_parameters(self):

        return "suite_parameter" in inspect.getargspec(self.get_function_object()).args

    def __not_ran(self, param, class_param):
        """
        :param param: test parameter
        :param class_param: class parameter
        :return: BOOLEAN, True if test has not ran yet, False otherwise
        """
        return str(class_param) not in self.metrics.get_metrics() or \
            str(param) not in self.metrics.get_metrics()[str(class_param)]

    def is_qualified_for_retry(self, param=None, class_param=None):

        if self.__not_ran(param, class_param):
            return True
        test = self.metrics.get_metrics()[str(class_param)][str(param)]
        if test["status"] in TestCategory.ALL_UN_SUCCESSFUL:
            if self.get_no_retry_on() and type(test["exceptions"][-1]) in self.get_no_retry_on():
                return False
            elif self.get_retry_on() and type(test["exceptions"][-1]) not in self.get_retry_on():
                return False
            return True
        return False

    def get_status(self, param, class_param):

        if self.__not_ran(param, class_param):
            return None
        return self.metrics.get_metrics()[str(class_param)][str(param)]["status"]

    def get_number_of_actual_retries(self, param, class_param):

        if self.__not_ran(param, class_param):
            return 0
        return self.metrics.get_metrics()[str(class_param)][str(param)]["retry"]


class Limiter:

    # honor limits or not
    ACTIVE = True

    # truncation limits
    __DEFAULT_LIMIT = 3000
    EXCEPTION_MESSAGE_LIMIT = __DEFAULT_LIMIT
    TRACEBACK_LIMIT = __DEFAULT_LIMIT

    # throttling limits
    SUITE_THROTTLING = 0  # only applies to parallels
    TEST_THROTTLING = 0  # only applies to parallels

    @staticmethod
    def parse_exception_object(value):

        if Limiter.ACTIVE and value is not None:
            msg = value.message if sys.version_info[0] < 3 else str(value)
            if isinstance(msg, str) and len(msg) > Limiter.EXCEPTION_MESSAGE_LIMIT:
                value.message = "{} [. . .]".format(msg[:Limiter.EXCEPTION_MESSAGE_LIMIT])
        return value

    @staticmethod
    def parse_traceback(value):

        if Limiter.ACTIVE and value is not None:
            if isinstance(value, str) and len(value) > Limiter.TRACEBACK_LIMIT:
                value = "{} [. . .]".format(value[:Limiter.TRACEBACK_LIMIT])
        return value

    @staticmethod
    def get_suite_throttling():
        return Limiter.SUITE_THROTTLING if Limiter.ACTIVE else 0

    @staticmethod
    def get_test_throttling():
        return Limiter.TEST_THROTTLING if Limiter.ACTIVE else 0


class GroupRulesObject(object):

    def __init__(self, definition):

        self.definition = definition

    def run_after_group(self, suite):

        for group, definition in self.definition.items():
            if suite.get_class_object() in definition["suites"]:
                definition["suites"].remove(suite.get_class_object())
                if not definition["suites"] and DecoratorType.AFTER_GROUP in definition["rules"]:
                    for func in definition["rules"][DecoratorType.AFTER_GROUP]:
                        try:
                            func["decorated_function"]()
                        except Exception as error:
                            trace = traceback.format_exc()
                            return {"trace": trace, "exception": error}
        return None

    def run_before_group(self, suite, rule_type):

        for group, definition in self.definition.items():
            if suite.get_class_object() in definition["suites"] and rule_type in definition["rules"]:
                for func in list(definition["rules"][rule_type]):
                    try:
                        func["decorated_function"]()
                        definition["rules"].pop(rule_type)
                    except Exception as error:
                        trace = traceback.format_exc()
                        return {group: {"trace": trace, "exception": error, "definition": definition}}
        return None
