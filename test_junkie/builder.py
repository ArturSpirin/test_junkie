import inspect
from test_junkie.listener import Listener
from test_junkie.rules import Rules


class Builder(object):

    __UNIQUE_TEST_SUITES = []
    __EXECUTION_ROSTER = {}
    __CURRENT_SUITE_OBJECT = None

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
            _function_name = decorated_function.__name__
        else:
            if decorated_function is not None:
                _class_name = decorated_function.__name__
                Builder.__CURRENT_SUITE_OBJECT["class_object"] = decorated_function
                Builder.__CURRENT_SUITE_OBJECT["class_retry"] = decorator_kwargs.get("retry", 1)
                Builder.__CURRENT_SUITE_OBJECT["class_skip"] = decorator_kwargs.get("skip", False)
                Builder.__CURRENT_SUITE_OBJECT["class_meta"] = decorator_kwargs.get("meta", None)
                Builder.__CURRENT_SUITE_OBJECT["test_listener"] = decorator_kwargs.get("listener", Listener)
                Builder.__CURRENT_SUITE_OBJECT["test_rules"] = decorator_kwargs.get("rules", Rules)
                Builder.__CURRENT_SUITE_OBJECT["pr"] = decorator_kwargs.get("pr", [])
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
