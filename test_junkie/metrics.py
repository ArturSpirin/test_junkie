import errno
import multiprocessing
import os
import sys
import threading
import time
import traceback
from datetime import datetime

import pkg_resources

from test_junkie.cli.cli import CliUtils

from test_junkie.cli.cli_config import Config
from test_junkie.debugger import LogJunkie
from test_junkie.decorators import DecoratorType
from test_junkie.constants import SuiteCategory, TestCategory, DocumentationLinks


class ClassMetrics(object):

    def __init__(self):

        self.__stats = {"status": None, "retry": 0, "runtime": 0, "start": None, "end": None,
                        DecoratorType.BEFORE_CLASS: {"performance": [], "exceptions": [], "tracebacks": []},
                        DecoratorType.BEFORE_TEST: {"performance": [], "exceptions": [], "tracebacks": []},
                        DecoratorType.AFTER_TEST: {"performance": [], "exceptions": [], "tracebacks": []},
                        DecoratorType.AFTER_CLASS: {"performance": [], "exceptions": [], "tracebacks": []}}

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def update_decorator_metrics(self, decorator, start_time, exception=None, trace=None):
        from test_junkie.objects import Limiter
        self.__stats[decorator]["performance"].append(time.time() - start_time)
        self.__stats[decorator]["exceptions"].append(Limiter.parse_exception_object(exception))
        self.__stats[decorator]["tracebacks"].append(Limiter.parse_traceback(trace))

    def update_suite_metrics(self, status, start_time, initiation_error=None):

        self.__stats["status"] = status
        if status not in [SuiteCategory.CANCEL, SuiteCategory.SKIP, SuiteCategory.IGNORE]:
            self.__stats["retry"] += 1
        self.__stats["start"] = start_time
        self.__stats["end"] = time.time()
        self.__stats["runtime"] = self.__stats["end"] - self.__stats["start"]
        if status in [SuiteCategory.IGNORE] and initiation_error is not None:
            self.__stats.update({"initiation_error": initiation_error})

    def get_metrics(self):

        return self.__stats

    def __get_average_metric(self, decorator, metric):

        from statistics import mean
        performance = self.get_metrics().get(decorator, {}).get(metric, None)
        return mean(performance) if performance else None

    def get_average_performance_of_after_class(self):
        return self.__get_average_metric(DecoratorType.AFTER_CLASS, "performance")

    def get_average_performance_of_before_class(self):
        return self.__get_average_metric(DecoratorType.BEFORE_CLASS, "performance")

    def get_average_performance_of_after_test(self):
        return self.__get_average_metric(DecoratorType.AFTER_TEST, "performance")

    def get_average_performance_of_before_test(self):
        return self.__get_average_metric(DecoratorType.BEFORE_TEST, "performance")


class TestMetrics(object):

    def __init__(self):

        self.__stats = {}

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def update_metrics(self, status, start_time, param=None, class_param=None, exception=None,
                       formatted_traceback=None, runtime=None, decorator=None):

        def __get_template():

            return {"status": None,
                    "retry": 0,
                    "performance": [],
                    "exceptions": [],
                    "tracebacks": [],
                    "statuses": [],
                    DecoratorType.BEFORE_TEST: {"performance": [], "exceptions": [], "tracebacks": []},
                    DecoratorType.AFTER_TEST: {"performance": [], "exceptions": [], "tracebacks": []}}

        runtime = runtime if runtime is not None else time.time() - start_time
        string_param = str(param)
        string_class_param = str(class_param)
        if string_class_param not in self.__stats:
            self.__stats.update({string_class_param: {string_param: __get_template()}})
        elif string_param not in self.__stats[string_class_param]:
            self.__stats[string_class_param].update({string_param: __get_template()})

        from test_junkie.objects import Limiter
        if decorator is not None:
            self.__stats[string_class_param][string_param][decorator]["performance"].append(time.time() - start_time)
            self.__stats[string_class_param][string_param][decorator]["exceptions"]\
                .append(Limiter.parse_exception_object(exception))
            self.__stats[string_class_param][string_param][decorator]["tracebacks"]\
                .append(Limiter.parse_traceback(formatted_traceback))

            if self.__stats[string_class_param][string_param]["status"] is None:
                # while status is not set, will use one that is currently passed in
                # Once its explicitly updated for the test decorator, then we wont change it
                self.__stats[string_class_param][string_param]["status"] = status
        else:
            self.__stats[string_class_param][string_param]["performance"].append(runtime)
            self.__stats[string_class_param][string_param]["exceptions"]\
                .append(Limiter.parse_exception_object(exception))
            self.__stats[string_class_param][string_param]["tracebacks"]\
                .append(Limiter.parse_traceback(formatted_traceback))
            self.__stats[string_class_param][string_param]["retry"] += 1
            self.__stats[string_class_param][string_param]["status"] = status
            self.__stats[string_class_param][string_param]["param"] = param
            self.__stats[string_class_param][string_param]["class_param"] = class_param
            self.__stats[string_class_param][string_param]["statuses"].append(status)

    def get_metrics(self):

        return self.__stats


class Aggregator(object):

    def __init__(self, executed_suites):

        self.__executed_suites = executed_suites

    @property
    def executed_suites(self):
        return self.__executed_suites

    @staticmethod
    def percentage(total, part):
        if part > 0:
            return "{:0.2f}".format(float(part) / float(total) * 100)
        else:
            return "0"

    def get_basic_report(self):

        def get_template():

            return {"total": 0,
                    TestCategory.SUCCESS: 0,
                    TestCategory.FAIL: 0,
                    TestCategory.ERROR: 0,
                    TestCategory.IGNORE: 0,
                    TestCategory.SKIP: 0,
                    TestCategory.CANCEL: 0}

        report = {"tests": get_template(),
                  "suites": {}}

        for suite in self.__executed_suites:
            if suite not in report["suites"]:
                report["suites"].update({suite: get_template()})
            for test in suite.get_test_objects():
                test_metrics = test.metrics.get_metrics()
                for class_param, class_param_data in test_metrics.items():
                    for param, param_data in class_param_data.items():
                        report["tests"]["total"] += 1
                        report["tests"][param_data["status"]] += 1
                        report["suites"][suite]["total"] += 1
                        report["suites"][suite][param_data["status"]] += 1
        return report

    def get_report_by_features(self):

        report = {}
        for suite in self.__executed_suites:
            feature = suite.get_feature()
            if feature not in report:
                report.update({feature: {"_totals_": Aggregator.get_template()}})
            for test in suite.get_test_objects():
                component = test.get_component()
                if component not in report[feature]:
                    report[feature].update({component: Aggregator.get_template()})
                test_metrics = test.metrics.get_metrics()
                Aggregator._update_report(report, test_metrics, feature, component)
        return report

    def get_report_by_tags(self):

        report = {}
        for suite in self.__executed_suites:
            tag_metrics = suite.get_data_by_tags()
            for metric, metric_data in tag_metrics.items():
                if metric == "_totals_":
                    continue
                metric = metric if metric is not None else "Not Defined"
                if metric not in report:
                    report.update({metric: Aggregator.get_template()})
                for entry in metric_data["performance"]:
                    report[metric]["performance"].append(entry)
                for entry in metric_data["exceptions"]:
                    if entry is not None:
                        report[metric]["exceptions"].append(entry)
                for retry in metric_data["retries"]:
                    report[metric]["retries"].append(retry)
                report[metric]["total"] += metric_data["total"]
                for status in TestCategory.ALL:
                    report[metric][status] += metric_data[status]
        return report

    def get_report_by_owner(self):

        report = {"_totals_": Aggregator.get_template()}
        for suite in self.__executed_suites:
            for test in suite.get_test_objects():
                owner = test.get_owner()
                if owner not in report:
                    report.update({owner: Aggregator.get_template()})
                test_metrics = test.metrics.get_metrics()
                Aggregator._update_report(report, test_metrics, owner)
        return report

    def get_report_by_suite(self):

        report = {"_totals_": Aggregator.get_template()}
        for suite in self.__executed_suites:
            suite_name = suite.get_class_name()
            for test in suite.get_test_objects():
                if suite_name not in report:
                    report.update({suite_name: Aggregator.get_template()})
                test_metrics = test.metrics.get_metrics()
                Aggregator._update_report(report, test_metrics, suite_name)
        return report

    @staticmethod
    def _update_report(report, metrics, category, subcategory=0):

        for class_param, class_param_data in metrics.items():
            for param, data in class_param_data.items():
                for entry in data["performance"]:
                    if subcategory == 0:
                        report[category]["performance"].append(entry)
                        report["_totals_"]["performance"].append(entry)
                    else:
                        report[category][subcategory]["performance"].append(entry)
                        report[category]["_totals_"]["performance"].append(entry)
                for entry in data["exceptions"]:
                    if entry is not None:
                        if subcategory == 0:
                            report[category]["exceptions"].append(entry)
                            report["_totals_"]["exceptions"].append(entry)
                        else:
                            report[category][subcategory]["exceptions"].append(entry)
                            report[category]["_totals_"]["exceptions"].append(entry)
                if subcategory == 0:
                    report[category]["retries"].append(data["retry"])
                    report["_totals_"]["retries"].append(data["retry"])
                    report[category]["total"] += 1
                    report["_totals_"]["total"] += 1
                    report[category][data["status"]] += 1
                    report["_totals_"][data["status"]] += 1
                else:
                    report[category][subcategory]["retries"].append(data["retry"])
                    report[category]["_totals_"]["retries"].append(data["retry"])
                    report[category][subcategory]["total"] += 1
                    report[category]["_totals_"]["total"] += 1
                    report[category][subcategory][data["status"]] += 1
                    report[category]["_totals_"][data["status"]] += 1

        return report

    @staticmethod
    def present_console_output(aggregator):

        def parse_exception(value):
            if value is not None:
                error = ""
                for line in value.split("\n"):
                    error += "\n\t\t  {}".format(line)
                return error

        report = aggregator.get_basic_report()
        test_report = report["tests"]
        suite_report = report["suites"]
        for status in TestCategory.ALL:
            value = "[{part}/{total} {percent}%] {status}".format(part=test_report[status],
                                                                  total=test_report["total"],
                                                                  status=status.upper(),
                                                                  percent=Aggregator.percentage(test_report["total"],
                                                                                                test_report[status]))
            if test_report[status]:
                value = CliUtils.format_bold_string(value)
            print(value)
        print("")
        for suite, stats in suite_report.items():
            status = suite.metrics.get_metrics()["status"]
            if status is None:  # this means that something went wrong with custom event processing
                status = "*"+SuiteCategory.ERROR
            print(">> [{status}] [{passed}/{total} {rate}%] [{runtime:0.2f}s] {module}.{name}"
                  .format(module=CliUtils.format_bold_string(suite.get_class_module()),
                          name=CliUtils.format_bold_string(suite.get_class_name()),
                          status=CliUtils.format_bold_string(status.upper()),
                          runtime=suite.get_runtime(),
                          rate=Aggregator.percentage(stats["total"], stats[TestCategory.SUCCESS]),
                          passed=stats[TestCategory.SUCCESS],
                          total=stats["total"]))
            if status == SuiteCategory.IGNORE:
                print("\t|__ reason: {error}".format(error=suite.metrics.get_metrics().get("initiation_error", None)))
            if status != SuiteCategory.SUCCESS:
                tests = suite.get_unsuccessful_tests()
                for test in tests:
                    test_metrics = test.metrics.get_metrics()
                    print("\t|__ test: {name}()".format(name=CliUtils.format_bold_string(test.get_function_name())))
                    for class_param, class_param_data in test_metrics.items():
                        if class_param != "None":
                            print("\t  |__ class parameter: {class_parameter}".format(class_parameter=class_param))
                        for param, param_data in class_param_data.items():
                            if param != "None":
                                print("\t    |__ parameter: {parameter}".format(parameter=param))
                            for index in range(param_data["retry"]):
                                trace = param_data["tracebacks"][index]
                                if trace is not None:
                                    trace = ":: Traceback: {}".format(CliUtils.format_color_string(
                                        parse_exception(trace.encode('utf8', errors="replace").decode("utf8")), "red"))
                                else:
                                    trace = ""
                                print("\t      |__ run #{num} [{status}] [{runtime:0.2f}s] {trace}"
                                      .format(num=index + 1,
                                              trace=trace,
                                              runtime=param_data["performance"][index],
                                              status=param_data["statuses"][index].upper()))
        print("\n===========================================================")
        print(". Test Junkie {} (Python{}) {} .".format(pkg_resources.require("test-junkie")[0].version,
                                                        sys.version_info[0],
                                                        DocumentationLinks.DOMAIN))
        print("===========================================================")

    @staticmethod
    def get_template():

        return {"performance": [],
                "exceptions": [],
                "retries": [],
                "total": 0,
                TestCategory.SUCCESS: 0,
                TestCategory.SKIP: 0,
                TestCategory.FAIL: 0,
                TestCategory.CANCEL: 0,
                TestCategory.IGNORE: 0,
                TestCategory.ERROR: 0}

    def get_average_test_runtime(self):

        from statistics import mean
        samples = []
        for suite in self.__executed_suites:
            for test in suite.get_test_objects():
                test_metrics = test.metrics.get_metrics()
                for class_param, class_param_data in test_metrics.items():
                    for param, param_data in class_param_data.items():
                        samples.append(mean(param_data["performance"]))
        return mean(samples) if samples else None


class ResourceMonitor(threading.Thread):

    def __init__(self):

        self.file_path = "{dir}{sep}.resources_{timestamp}".format(dir=Config.get_root_dir(),
                                                                   sep=os.sep,
                                                                   timestamp=time.time())

        threading.Thread.__init__(self)
        self.exit = multiprocessing.Event()

    def get_file_path(self):

        return self.file_path

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def run(self):
        import psutil
        self.mkdir_p(Config.get_root_dir())
        with open(self.file_path, "w+") as records:
            records.write("")
        while not self.exit.is_set():
            time.sleep(1)
            data = "{timestamp}, {cpu}, {memory}\n".format(timestamp=datetime.now(),
                                                           cpu=psutil.cpu_percent(),
                                                           memory=psutil.virtual_memory().percent)
            with open(self.file_path, "a+") as records:
                records.write(data)

    def shutdown(self):
        self.exit.set()

    def cleanup(self):
        try:
            os.remove(self.file_path)
        except:
            LogJunkie.error(traceback.format_exc())
