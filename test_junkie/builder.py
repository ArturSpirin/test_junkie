import hashlib
import inspect

from test_junkie.constants import DocumentationLinks
from test_junkie.errors import BadParameters, BadSignature
from test_junkie.listener import Listener
from test_junkie.rules import Rules


class Builder(object):

    __TEST_ID = 0  # unique but not persistent from execution to execution
    __SUITE_ID = 0  # unique but not persistent from execution to execution

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

    __GROUP_RULES = []
    __GROUP_RULE_DEFINITIONS = {}
    __REQUESTED_SUITES = None
    __FILE_CONTROL = None  # this controls the cross file test injections

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
    def build_group_definitions(suites):

        Builder.__REQUESTED_SUITES = suites
        for group_rule in Builder.__GROUP_RULES:
            func = group_rule["decorated_function"]
            func(func)
        from test_junkie.objects import GroupRulesObject
        return GroupRulesObject(Builder.__GROUP_RULE_DEFINITIONS)

    @staticmethod
    def register_group_rules(decorated_function, decorator_kwargs, decorator_type):

        Builder.__GROUP_RULES.append({"decorated_function": decorated_function,
                                      "decorator_kwargs": decorator_kwargs,
                                      "decorator_type": decorator_type})

    @staticmethod
    def add_group_rule(suites, decorated_function, decorator_kwargs, decorator_type):

        if not suites or not isinstance(suites, list):
            raise BadParameters("Group Rules must be defined with a mandatory argument \"suites\" which must be "
                                "of type {}. Please see documentation: {}".format(list, DocumentationLinks.GROUP_RULES))
        suites = sorted(set(suites), key=lambda x: str(x), reverse=True)
        for suite in list(suites):
            if suite not in Builder.__REQUESTED_SUITES:
                suites.remove(suite)
        if suites:  # making sure that rules only apply when we actually run applicable test suites
            group = hashlib.md5(str(suites).encode("utf8")).hexdigest()
            if group not in Builder.__GROUP_RULE_DEFINITIONS:
                Builder.__GROUP_RULE_DEFINITIONS.update({group: {"suites": suites, "rules": {}}})
            if decorator_type not in Builder.__GROUP_RULE_DEFINITIONS[group]["rules"]:
                Builder.__GROUP_RULE_DEFINITIONS[group]["rules"].update({decorator_type: []})
            Builder.__GROUP_RULE_DEFINITIONS[group]["rules"][decorator_type].append(
                {"decorated_function": decorated_function, "decorator_kwargs": decorator_kwargs})

    @staticmethod
    def build_suite_definitions(decorated_function, decorator_kwargs, decorator_type):
        from test_junkie.decorators import DecoratorType
        from test_junkie.debugger import LogJunkie
        from test_junkie.objects import SuiteObject

        if decorator_type == DecoratorType.TEST_CASE:
            Builder.__TEST_ID += 1
        elif decorator_type == DecoratorType.TEST_SUITE:
            Builder.__SUITE_ID += 1

        _function_name = None
        _class_name = None
        if inspect.isfunction(decorated_function):
            decorator_kwargs.update({"testjunkie_test_id": Builder.__TEST_ID,
                                     "testjunkie_suite_id": Builder.__SUITE_ID})
            Builder.__validate_test_kwargs(decorator_kwargs, decorated_function)
            _function_name = decorated_function.__name__
            if Builder.__FILE_CONTROL is not None \
                    and Builder.__FILE_CONTROL != inspect.getsourcefile(decorated_function):
                Builder.__set_current_suite_object_defaults()
            Builder.__FILE_CONTROL = inspect.getsourcefile(decorated_function)
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
                decorator_kwargs.update({"testjunkie_suite_id": Builder.__SUITE_ID})
                Builder.__CURRENT_SUITE_OBJECT["decorator_kwargs"] = decorator_kwargs

        if Builder.__CURRENT_SUITE_OBJECT is None:
            Builder.__set_current_suite_object_defaults()
        elif Builder.__CURRENT_SUITE_OBJECT.get("class_name", None) is None:
            Builder.__CURRENT_SUITE_OBJECT["class_name"] = _class_name

        if _function_name is not None:
            Builder.__CURRENT_SUITE_OBJECT["suite_definition"][decorator_type].append(
                {"decorated_function": decorated_function, "decorator_kwargs": decorator_kwargs})
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

        def validation_failed(actual, expected):
            if expected == "<type 'function'>":
                if inspect.isfunction(actual) or inspect.ismethod(actual):
                    return False
            else:
                if inspect.isclass(actual) and issubclass(actual, expected):
                    return False
                if type(actual) is expected or isinstance(actual, expected):
                    return False
            return True

        args = Builder.__SUITE_VALIDATION_ARGS if suite else Builder.__TEST_VALIDATION_ARGS
        for arg, expected_types in args.items():
            failed = True
            if arg in kwargs:
                for expected_type in expected_types:
                    if failed:
                        failed = validation_failed(kwargs.get(arg), expected_type)
                if failed:
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
    def __validate_test_kwargs(kwargs, decorated_function):
        data = Builder.__validation_failed(kwargs, suite=False)
        if data:
            raise BadParameters("Argument: \"{}\" in @test() decorator must be of either type: {} but found: {}. "
                                "For more info, see @test() decorator documentation: {}"
                                .format(data["arg"], data["expected"], data["actual"],
                                        DocumentationLinks.TEST_DECORATOR))
        if "parameter" not in inspect.getargspec(decorated_function).args and kwargs.get("parameters") is not None:
            raise BadSignature("When using \"parameters\" argument for @test() decorator, "
                               "you must accept \"parameter\" in the function's signature. "
                               "For more info, see documentation: {}"
                               .format(DocumentationLinks.PARAMETERIZED_TESTS))
