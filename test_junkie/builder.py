import inspect

from test_junkie.constants import DocumentationLinks
from test_junkie.errors import BadParameters
from test_junkie.listener import Listener
from test_junkie.rules import Rules


class Builder(object):

    __UNIQUE_TEST_SUITES = []
    __EXECUTION_ROSTER = {}
    __CURRENT_SUITE_OBJECT = None
    __SUITE_VALIDATION_ARGS = {"owner": [str], "meta": [dict], "retry": [int], "listener": [Listener], "rules": [Rules],
                               "parallelized": [bool], "priority": [int], "feature": [str], "pr": [list],
                               "parameters": ["<type 'function'>", list], "skip": ["<type 'function'>", bool]}
    __TEST_VALIDATION_ARGS = {"owner": [str], "meta": [dict], "retry": [int], "parallelized_parameters": [bool],
                              "parallelized": [bool], "priority": [int], "component": [str], "tags": [list],
                              "no_retry_on": [list], "retry_on": [list], "pr": [list],
                              "parameters": ["<type 'function'>", list], "skip": ["<type 'function'>", bool]}

    @staticmethod
    def get_execution_roster():
        return Builder.__EXECUTION_ROSTER

    @staticmethod
    def __set_current_suite_object_defaults():
        from test_junkie.decorators import DecoratorType
        Builder.__CURRENT_SUITE_OBJECT = {"test_listener": None,
                                          "test_rules": None,
                                          "class_name": None,
                                          "class_retry": None,
                                          "class_skip": False,
                                          "class_object": None,
                                          "suite_definition": {DecoratorType.BEFORE_CLASS: [],
                                                               DecoratorType.BEFORE_TEST: [],
                                                               DecoratorType.TEST_CASE: [],
                                                               DecoratorType.AFTER_TEST: [],
                                                               DecoratorType.AFTER_CLASS: []}}

    @staticmethod
    def build_suite_definitions(decorated_function, decorator_kwargs, decorator_type):
        from test_junkie.debugger import LogJunkie
        from test_junkie.objects import SuiteObject
        _function_name = None
        _class_name = None
        if inspect.isfunction(decorated_function):
            Builder.__validate_test_kwargs(decorator_kwargs)
            _function_name = decorated_function.__name__
        else:
            if decorated_function is not None:
                Builder.__validate_suite_kwargs(decorator_kwargs)
                _class_name = decorated_function.__name__
                Builder.__CURRENT_SUITE_OBJECT["class_object"] = decorated_function
                Builder.__CURRENT_SUITE_OBJECT["class_retry"] = decorator_kwargs.get("retry", 1)
                Builder.__CURRENT_SUITE_OBJECT["class_skip"] = decorator_kwargs.get("skip", False)
                Builder.__CURRENT_SUITE_OBJECT["class_meta"] = decorator_kwargs.get("meta", {})
                Builder.__CURRENT_SUITE_OBJECT["test_listener"] = decorator_kwargs.get("listener", Listener)
                Builder.__CURRENT_SUITE_OBJECT["test_rules"] = decorator_kwargs.get("rules", Rules)
                Builder.__CURRENT_SUITE_OBJECT["class_parameters"] = decorator_kwargs.get("parameters", [None])
                Builder.__CURRENT_SUITE_OBJECT["parallelized"] = decorator_kwargs.get("parallelized", True)
                Builder.__CURRENT_SUITE_OBJECT["decorator_kwargs"] = decorator_kwargs

        if Builder.__CURRENT_SUITE_OBJECT is None:
            Builder.__set_current_suite_object_defaults()
        elif Builder.__CURRENT_SUITE_OBJECT.get("class_name", None) is None:
            Builder.__CURRENT_SUITE_OBJECT["class_name"] = _class_name

        if _function_name is not None:
            Builder.__CURRENT_SUITE_OBJECT["suite_definition"][decorator_type]\
                        .append({"decorated_function": decorated_function, "decorator_kwargs": decorator_kwargs})
            LogJunkie.debug("=======================Suite Definition Updated=============================")
            LogJunkie.debug("Function: {}".format(_function_name))
            LogJunkie.debug("Decorator Type: {}".format(decorator_type))
            LogJunkie.debug("Decorator Arguments: {}".format(decorator_kwargs))
            LogJunkie.debug("Function object: {}".format(decorated_function))
            LogJunkie.debug("============================================================================")
        else:
            LogJunkie.debug("=======================Suite Definition Finished=============================")
            LogJunkie.debug("Suite: {}".format(_class_name))
            LogJunkie.debug("Suite Definition: {}".format(Builder.__CURRENT_SUITE_OBJECT))
            Builder.__EXECUTION_ROSTER.update({decorated_function: SuiteObject(Builder.__CURRENT_SUITE_OBJECT)})
            Builder.__set_current_suite_object_defaults()
            LogJunkie.debug(">> Definition reset for next suite <<")
            LogJunkie.debug("=============================================================================\n\n")

    # noinspection PyTypeHints
    @staticmethod
    def __validation_failed(kwargs, suite=True):

        args = Builder.__SUITE_VALIDATION_ARGS if suite else Builder.__TEST_VALIDATION_ARGS
        for arg, expected_types in args.items():
            if arg in kwargs:
                for expected_type in expected_types:
                    if expected_type == "<type 'function'>":
                        if inspect.isfunction(kwargs.get(arg)) or inspect.ismethod(kwargs.get(arg)):
                            return False
                    else:
                        if inspect.isclass(kwargs.get(arg)) and issubclass(kwargs.get(arg), expected_type):
                            return False
                        if type(kwargs.get(arg)) is expected_type or isinstance(kwargs.get(arg), expected_type):
                            return False
                return {"expected": expected_types, "actual": type(kwargs.get(arg)), "arg": arg}
        return False

    @staticmethod
    def __validate_suite_kwargs(kwargs):

        data = Builder.__validation_failed(kwargs)
        if data:
            raise BadParameters("Argument: \"{}\" in @Suite() decorator must be of either type: {} but found: {}. "
                                "For more info, see @Suite() decorator documentation: {}"
                                .format(data["arg"], data["expected"], data["actual"],
                                        DocumentationLinks.SUITE_DECORATOR))

    @staticmethod
    def __validate_test_kwargs(kwargs):
        data = Builder.__validation_failed(kwargs, suite=False)
        if data:
            raise BadParameters("Argument: \"{}\" in @test() decorator must be of either type: {} but found: {}. "
                                "For more info, see @test() decorator documentation: {}"
                                .format(data["arg"], data["expected"], data["actual"],
                                        DocumentationLinks.TEST_DECORATOR))
