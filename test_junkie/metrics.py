import errno
import os
import sys
import threading
import time
import traceback
from datetime import datetime

from test_junkie.cli.cli_config import Config
from test_junkie.debugger import LogJunkie
from test_junkie.decorators import DecoratorType
from test_junkie.constants import SuiteCategory, TestCategory
from test_junkie.params import param_key


class ClassMetrics(object):

    def __init__(self):

        self.__stats = {"status": None, "retry": 0, "runtime": 0, "start": None, "end": None,
                        DecoratorType.BEFORE_CLASS: {"performance": [], "exceptions": [], "tracebacks": []},
                        DecoratorType.BEFORE_TEST: {"performance": [], "exceptions": [], "tracebacks": []},
                        DecoratorType.AFTER_TEST: {"performance": [], "exceptions": [], "tracebacks": []},
                        DecoratorType.AFTER_CLASS: {"performance": [], "exceptions": [], "tracebacks": []}}
        self.__outputs = []  # (output, log lines) printed outside of tests: @beforeClass, @afterClass, rules
        self.__listener_errors = []  # one dict per listener call that raised, see record_listener_error()

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def reset(self):
        # so a new Runner run doesn't inherit stale results from a previous one (fixes ticket: #43)
        self.__init__()

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

    def record_output(self, output, log):
        self.__outputs.append((output, log))

    def get_outputs(self):
        return self.__outputs

    def record_listener_error(self, event, test, param, class_param, exception, trace):
        """
        A listener call that raised. The run carries on and run() raises TestListenerError once it's over
        :param event: STRING, the listener function, e.g. "on_success"
        :param test: TestObject or None for suite events
        """
        self.__listener_errors.append({"event": event, "test": test, "param": param, "class_param": class_param,
                                       "exception": exception, "trace": trace})

    def get_listener_errors(self):
        return self.__listener_errors

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
        # (class param, param) -> [(run number, output, log lines), ...] for runs that printed or logged something.
        # Kept out of __stats so its shape stays as is
        self.__outputs = {}
        # (class param, param) -> [{"run", "policy", "when", "waited"}, ...]: one entry per retry, see record_retry()
        self.__retries = {}
        # class param -> [{"seconds", "with"}, ...]: time spent waiting for conflicting tests (conflicts_with=)
        self.__conflict_waits = {}

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def reset(self):
        # so a new Runner run doesn't inherit stale results from a previous one (fixes ticket: #43)
        self.__init__()

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
        string_param = param_key(param)
        string_class_param = param_key(class_param)
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
            if start_time is not None:
                if "start" not in self.__stats[string_class_param][string_param]:
                    self.__stats[string_class_param][string_param]["start"] = start_time
                self.__stats[string_class_param][string_param]["end"] = start_time + (runtime or 0)

    def get_metrics(self):

        return self.__stats

    def record_output(self, param, class_param, run, output, log):
        """
        What a run of this test printed or logged while it was captured (see test_junkie/console.py)
        """
        if output or log:
            self.__outputs.setdefault((param_key(class_param), param_key(param)), []).append((run, output, log))

    def get_outputs(self, param, class_param):
        """
        :return: LIST of (run number, output STRING, log lines LIST), oldest first - only runs that had any
        """
        return self.__outputs.get((param_key(class_param), param_key(param)), [])

    def record_retry(self, param, class_param, run, policy, when, waited):
        """
        A retry of this test: `run` is the run that failed (counting from 1 across the test's runs), `policy` the
        RetryPolicy name, `when` what matched (a When label, or None for plain retry=N), `waited` seconds slept.
        """
        self.__retries.setdefault((param_key(class_param), param_key(param)), []).append(
            {"run": run, "policy": policy, "when": when, "waited": waited})

    def record_conflict_wait(self, class_param, seconds, blockers):
        self.__conflict_waits.setdefault(param_key(class_param), []).append(
            {"seconds": round(seconds, 3), "with": list(blockers)})

    def get_conflict_waits(self, class_param):
        """:return: LIST of {"seconds", "with"} for waits under this suite parameter, oldest first"""
        return self.__conflict_waits.get(param_key(class_param), [])

    def get_retries(self, param, class_param):
        """:return: LIST of the dicts record_retry() stored, oldest first"""
        return self.__retries.get((param_key(class_param), param_key(param)), [])

    def is_flaky(self, param, class_param):
        """True if these parameters passed in the end after at least one failed or errored run"""
        return is_flaky(self.__stats.get(param_key(class_param), {}).get(param_key(param)))


def is_flaky(data):
    """data: one parameter slot of get_metrics(). Passed on its last run, failed or errored on an earlier one"""
    if not data or data.get("status") != TestCategory.SUCCESS:
        return False
    return any(status in (TestCategory.FAIL, TestCategory.ERROR) for status in (data.get("statuses") or [])[:-1])


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

            return {
                "total": 0,
                TestCategory.SUCCESS: 0,
                TestCategory.FAIL: 0,
                TestCategory.ERROR: 0,
                TestCategory.IGNORE: 0,
                TestCategory.SKIP: 0,
                TestCategory.CANCEL: 0
            }

        report = {
            "tests": dict(get_template()),
            "suites": {}
        }

        for suite in self.__executed_suites:

            if suite not in report["suites"]:
                report["suites"].update({suite: dict(get_template())})

            for test in suite.get_test_objects():

                test_metrics = test.metrics.get_metrics()

                for class_param, class_param_data in test_metrics.items():

                    for param, param_data in class_param_data.items():

                        if param_data["status"] is None:
                            continue  # never got a final status, nothing to count yet

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
                if data["status"] is None:
                    continue
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
        """
        Prints the problems, the summary and the verdict for these results - what tj run prints at the end of a run
        """
        from test_junkie.console import Console
        console = Console(None, mode="report")
        console.start(list(aggregator.executed_suites))
        console.finish(aggregator, sum(suite.get_runtime() or 0 for suite in aggregator.executed_suites))

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

    # seconds between samples - 1s gave the console chart only a few points for a short run
    INTERVAL = 0.25

    def __init__(self):

        self.file_path = "{dir}{sep}.resources_{timestamp}".format(dir=Config.get_root_dir(),
                                                                   sep=os.sep,
                                                                   timestamp=time.time())

        threading.Thread.__init__(self, daemon=True)
        self.exit = threading.Event()
        self.samples = []  # (time.time(), cpu %, memory %) - what tj run -m charts after the summary

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
        psutil.cpu_percent()  # the first call has nothing to compare with and always returns 0.0
        # wait() instead of sleep(): returns the moment shutdown() is called, and nothing is written after that
        while not self.exit.wait(ResourceMonitor.INTERVAL):
            now, cpu, memory = time.time(), psutil.cpu_percent(), psutil.virtual_memory().percent
            self.samples.append((now, cpu, memory))
            data = "{timestamp}, {cpu}, {memory}\n".format(timestamp=datetime.fromtimestamp(now), cpu=cpu,
                                                           memory=memory)
            with open(self.file_path, "a+") as records:
                records.write(data)

    def shutdown(self):
        self.exit.set()
        # wait for the thread - it used to keep running and could re-create the temp file after cleanup() removed it
        if self.is_alive():
            self.join(timeout=5)

    def cleanup(self):
        try:
            os.remove(self.file_path)
        except Exception:
            trace = traceback.format_exc()
            print("[WARNING] Failed to remove resource monitoring temp file: {}\n{}"
                  .format(self.file_path, trace), file=sys.stderr)
            LogJunkie.error(trace)
