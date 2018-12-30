import copy
import inspect
import traceback

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


class SuiteObject:

    def __init__(self, suite_definition):

        self.__suite_definition = suite_definition
        self.__listener = suite_definition["test_listener"](class_meta=suite_definition["class_meta"])
        self.__rules = suite_definition["test_rules"](class_meta=suite_definition["test_rules"])
        self.__tests = []
        for test in suite_definition["suite_definition"].get(DecoratorType.TEST_CASE):
            self.__tests.append(TestObject(test))
        self.metrics = ClassMetrics()

    def get_decorated_definition(self, decorator_type):

        return self.__suite_definition["suite_definition"].get(decorator_type)

    def get_test_count(self):

        return len(self.__tests)

    def get_class_name(self):

        return self.__suite_definition["class_name"]

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

        return self.__tests

    def get_skip(self):
        return self.__suite_definition.get("class_skip", False)

    def can_skip(self, features=None):

        can_skip = _FuncEval.eval_skip(self)
        if features is not None and can_skip is False:
            return not self.get_feature() in features
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


class TestObject:

    def __init__(self, test_definition):

        self.__test_definition = test_definition

        self.metrics = TestMetrics()

    def get_skip(self):
        return self.get_kwargs().get("skip", False)

    def can_skip(self):
        return _FuncEval.eval_skip(self)

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
            if self.get_no_retry_on() or self.get_retry_on():
                if type(test["exceptions"][-1]) in self.get_no_retry_on() or \
                        type(test["exceptions"][-1]) not in self.get_retry_on():
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
