import time

from test_junkie.decorators import DecoratorType
from test_junkie.constants import SuiteCategory


class ClassMetrics:

    def __init__(self):

        self.__stats = {"status": None, "retry": 0, "runtime": 0,
                        DecoratorType.BEFORE_CLASS: {"performance": [], "exceptions": []},
                        DecoratorType.BEFORE_TEST: {"performance": [], "exceptions": []},
                        DecoratorType.AFTER_TEST: {"performance": [], "exceptions": []},
                        DecoratorType.AFTER_CLASS: {"performance": [], "exceptions": []}}

    def update_decorator_metrics(self, decorator, start_time, exception=None):

        self.__stats[decorator]["performance"].append(time.time() - start_time)
        self.__stats[decorator]["exceptions"].append(exception)

    def update_suite_metrics(self, status, start_time):

        self.__stats["status"] = status
        if status not in [SuiteCategory.CANCEL, SuiteCategory.SKIP]:
            self.__stats["retry"] += 1
        self.__stats["runtime"] = time.time() - start_time

    def get_metrics(self):

        return self.__stats


class TestMetrics:

    def __init__(self):

        self.__stats = {}

    def update_metrics(self, status, start_time, param=None, class_param=None, exception=None):
        string_param = str(param)
        string_class_param = str(class_param)
        if string_class_param not in self.__stats:
            self.__stats.update({string_class_param: {string_param: {"status": None,
                                                                     "retry": 0,
                                                                     "performance": [],
                                                                     "exceptions": []}}})
        elif string_param not in self.__stats[string_class_param]:
            self.__stats[string_class_param].update({string_param: {"status": None,
                                                                    "retry": 0,
                                                                    "performance": [],
                                                                    "exceptions": []}})
        self.__stats[string_class_param][string_param]["performance"].append(time.time() - start_time)
        self.__stats[string_class_param][string_param]["exceptions"].append(exception)
        self.__stats[string_class_param][string_param]["retry"] += 1
        self.__stats[string_class_param][string_param]["status"] = status
        self.__stats[string_class_param][string_param]["param"] = param
        self.__stats[string_class_param][string_param]["class_param"] = class_param

    def get_metrics(self):

        return self.__stats
