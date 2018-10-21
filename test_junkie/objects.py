import copy
import inspect

from test_junkie.decorators import DecoratorType
from test_junkie.constants import TestCategory
from test_junkie.metrics import ClassMetrics, TestMetrics


class SuiteObject:

    def __init__(self, suite_definition):

        self.__suite_definition = suite_definition
        self.__listener = suite_definition["test_listener"](class_meta=suite_definition["class_meta"])
        self.__rules = suite_definition["test_rules"](class_meta=suite_definition["test_rules"])
        self.__tests = []
        self.__absolute_test_count = 0
        self.__test_count = 0
        self.__has_parameterized_tests = False

        for test in suite_definition["suite_definition"].get(DecoratorType.TEST_CASE):
            params = test["decorator_kwargs"].get("parameters", [])
            self.__tests.append(TestObject(test))
            self.__absolute_test_count += len(params) if params else 1
            self.__test_count += 1
            self.__has_parameterized_tests = True if params else False
        self.__absolute_test_count *= len(suite_definition["class_parameters"])

        self.metrics = ClassMetrics()

    def get_decorated_definition(self, decorator_type):

        return self.__suite_definition["suite_definition"].get(decorator_type)

    def get_test_count(self):

        return self.__test_count

    def get_absolute_test_count(self):

        return self.__absolute_test_count

    def has_parameterised_tests(self):

        return self.__has_parameterized_tests

    def get_class_name(self):

        return self.__suite_definition["class_name"]

    def get_class_object(self):

        return self.__suite_definition["class_object"]

    def get_class_module(self):

        return self.get_class_object().__module__

    def update_test_meta(self, parameter=None, suite_parameter=None, **kwargs):

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

    def get_test_objects(self):

        return self.__tests

    def can_skip(self):

        return self.__suite_definition.get("class_skip", False)

    def get_retry_limit(self):

        return self.__suite_definition.get("class_retry", 1)

    def get_rules(self):

        return self.__rules

    def get_listener(self):

        return self.__listener

    def get_meta(self):

        return self.__suite_definition["class_meta"]

    def get_unsuccessful_tests(self):

        unsuccessful_tests = []
        tests = self.get_test_objects()
        for test in tests:
            for class_param, metrics in test.metrics.get_metrics().items():
                for value in metrics.values():
                    if value["status"] in TestCategory.ALL_UN_SUCCESSFUL:
                        unsuccessful_tests.append(test)
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

    def get_parallel_restrictions(self):

        return self.__suite_definition["pr"]

    def get_parameters(self):

        return self.__suite_definition["class_parameters"]

    def get_kwargs(self):

        return self.__suite_definition["decorator_kwargs"]

    def is_parallelized(self):

        return self.__suite_definition["parallelized"]


class TestObject:

    def __init__(self, test_definition):

        self.__test_definition = test_definition

        self.metrics = TestMetrics()

    def can_skip(self):

        return self.get_kwargs().get("skip", False)

    def get_parameters(self):

        return self.get_kwargs().get("parameters", [None])

    def get_retry_limit(self):

        return self.get_kwargs().get("retry", 1)

    def get_function_name(self):

        return self.get_function_object().__name__

    def get_function_object(self):

        return self.__test_definition["decorated_function"]

    def get_tags(self):

        return self.get_kwargs().get("tags", [])

    def get_meta(self, parameter=None, class_parameter=None):

        string_param = str(parameter)
        string_class_param = str(class_parameter)
        meta = self.get_kwargs().get("meta", {})

        if "original" not in meta:
            meta.update({"original": copy.deepcopy(meta)})

        if string_class_param not in meta:
            meta.update({string_class_param: {string_param: copy.deepcopy(meta["original"])}})

        if string_param not in meta[string_class_param]:
            meta[string_class_param].update({string_param: copy.deepcopy(meta["original"])})

        return meta[string_class_param][string_param]

    def get_kwargs(self):

        return self.__test_definition["decorator_kwargs"]

    def _is_qualified_for_retry(self, param=None, class_param=None):

        test = self.metrics.get_metrics()[str(class_param)][str(param)]
        return test["status"] in TestCategory.ALL_UN_SUCCESSFUL

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
