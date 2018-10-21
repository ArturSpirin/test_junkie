import time

from test_junkie.decorators import DecoratorType
from test_junkie.constants import SuiteCategory, TestCategory


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

    def get_metrics(self):

        return self.__stats


class StatsJunkie:

    def __init__(self, stats):

        self.__stats = stats

        self.__failed_tests = None
        self.__errored_tests = None
        self.__skipped_tests = None
        self.__ignored_tests = None
        self.__successful_tests = None

        self.__performance_metrics = None

    def get_size_of_execution_manifest(self):
        import sys
        return sys.getsizeof(self.__stats)

    def has_failed_tests(self):

        return self.get_failed_tests() is not None and len(self.get_failed_tests()) > 0

    def has_errored_tests(self):

        return self.get_errored_tests() is not None and len(self.get_errored_tests()) > 0

    def has_ignored_tests(self):

        return self.get_ignored_tests() is not None and len(self.get_ignored_tests()) > 0

    def has_passed_tests(self):

        return self.get_passed_tests() is not None and len(self.get_passed_tests()) > 0

    def has_unsuccessful_tests(self):

        return self.has_errored_tests() or self.has_failed_tests() or self.has_ignored_tests()

    def __get_tests(self, category):

        __mapping = {TestCategory.SUCCESS: self.__successful_tests,
                     TestCategory.FAIL: self.__failed_tests,
                     TestCategory.ERROR: self.__errored_tests,
                     TestCategory.SKIP: self.__skipped_tests,
                     TestCategory.IGNORE: self.__ignored_tests}

        __mapped_test_variable = __mapping[category]

        if __mapped_test_variable is None:
            tests = {}
            for class_object, data in self.__stats.items():
                recorded_tests = data.get(category, None)
                if recorded_tests is not None:
                    tests.update({class_object.__module__: []})

                    for test, metrics in recorded_tests.items():
                        for item in metrics:
                            tests[class_object.__module__].append({test.__name__: metrics[item]})
                    __mapped_test_variable = tests
        return __mapped_test_variable

    def get_failed_tests(self):

        return self.__get_tests(TestCategory.FAIL)

    def get_errored_tests(self):

        return self.__get_tests(TestCategory.ERROR)

    def get_ignored_tests(self):

        return self.__get_tests(TestCategory.IGNORE)

    def get_skipped_tests(self):

        return self.__get_tests(TestCategory.SKIP)

    def get_passed_tests(self):

        return self.__get_tests(TestCategory.SUCCESS)

    def get_unsuccessful_tests(self):

        unsuccessful_tests = {TestCategory.FAIL: self.get_failed_tests(),
                              TestCategory.ERROR: self.get_errored_tests(),
                              TestCategory.IGNORE: self.get_ignored_tests()}

        return unsuccessful_tests

    def get_all_tests(self):

        unsuccessful_tests = {TestCategory.FAIL: self.get_failed_tests(),
                              TestCategory.ERROR: self.get_errored_tests(),
                              TestCategory.IGNORE: self.get_ignored_tests(),
                              TestCategory.SKIP: self.get_skipped_tests(),
                              TestCategory.SUCCESS: self.get_passed_tests()}

        return unsuccessful_tests

    def get_unsuccessful_test_count(self):

        data = self.get_unsuccessful_tests()
        count = 0
        for category, category_data in data.items():
            if category_data:
                for suite, suite_data in category_data.items():
                    count += len(suite_data)
        return count

    def get_total_test_count(self):

        data = self.get_all_tests()
        count = 0
        for category, category_data in data.items():
            if category_data:
                for suite, suite_data in category_data.items():
                    count += len(suite_data)
        return count

    def get_performance_metrics(self):

        if self.__performance_metrics is None:
            __per_category = {TestCategory.SUCCESS: {"total": 0, "average": 0, "min": 0, "mean": 0, "max": 0},
                              TestCategory.FAIL: {"total": 0, "average": 0, "min": 0, "mean": 0, "max": 0},
                              TestCategory.ERROR: {"total": 0, "average": 0, "min": 0, "mean": 0, "max": 0},
                              TestCategory.IGNORE: {"total": 0, "average": 0, "min": 0, "mean": 0, "max": 0}}
            parsed_data = {"top_level": {}, "suite_level": {}}
            data = self.get_all_tests()
            for test_category, suites in data.items():
                if suites is not None:
                    for suite, suite_data in suites.items():
                        if suite not in parsed_data["suite_level"]:
                            print("adding suite")
                            parsed_data["suite_level"].update({suite: {"total_tests": 0,
                                                                       "failed_tests": 0,
                                                                       "ignored_tests": 0,
                                                                       "errored_tests": 0,
                                                                       "passed_tests": 0,
                                                                       "retries": {"total": 0,
                                                                                   "average": 0,
                                                                                   "per_category": __per_category},
                                                                       "performance": {"total": 0,
                                                                                       "average": 0,
                                                                                       "per_category": __per_category},
                                                                       "exceptions": []}})
                        for item in suite_data:
                            for test_name, test_metrics in item.items():
                                retries = test_metrics.get("retries")

                                parsed_data["suite_level"][suite]["retries"]["total"] += retries
                                parsed_data["suite_level"][suite]["retries"]["per_category"][test_category]["total"] += retries
                                performance = test_metrics.get("performance")
                                exceptions = test_metrics.get("exceptions")
                else:
                    print("There are no suites to parse for category: {}".format(test_category))
            self.__performance_metrics = parsed_data
        return self.__performance_metrics

    def get_average_retry_count(self):

        pass

    def get_average_test_performance(self):

        pass

    def get_average_before_class_performance(self):

        pass

    def get_average_after_class_performance(self):

        pass

    def get_average_before_test_performance(self):

        pass

    def get_average_after_test_performance(self):

        pass

    def get_most_common_exceptions(self, limit=5):

        pass
