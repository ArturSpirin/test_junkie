import copy
import json
import time
import traceback

from test_junkie.constants import TestCategory, DecoratorType, Color
from test_junkie.debugger import LogJunkie
from test_junkie.metrics import Aggregator
from test_junkie.reporter.analyzer import Analyzer
from test_junkie.reporter.html_template import ReportTemplate


class Reporter:

    @staticmethod
    def round(value):
        from statistics import mean
        if value:
            return str(float("{0:.2f}".format(float(mean(value)))))
        else:
            return "0"

    @staticmethod
    def total_up(value):
        if value:
            return str(float("{0:.2f}".format(float(sum(value)))))
        else:
            return "0"

    @staticmethod
    def escape(s, quote=True):
        """
        Copy of the HTML escape function to avoid python2 dependency
        """
        s = s.replace("&", "&amp;")  # Must be done first!
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        if quote:
            s = s.replace('"', "&quot;")
            s = s.replace('\'', "&#x27;")
        return s

    def __init__(self, monitoring_file, aggregator, runtime, multi_threading_enabled):

        self.analyzer = Analyzer(monitoring_enabled=monitoring_file, multi_threading_enabled=multi_threading_enabled)

        self.monitoring_file = monitoring_file
        self.aggregator = aggregator
        self.runtime = runtime

        self.features = aggregator.get_report_by_features()
        self.tags = aggregator.get_report_by_tags()
        self.test_totals = aggregator.get_basic_report()["tests"]
        self.owners = aggregator.get_report_by_owner()
        self.suites = aggregator.get_report_by_suite()
        self.average_runtime = aggregator.get_average_test_runtime()

        self.__processed_resources = {}
        self.__cpu_average = "Unknown"
        self.__mem_average = "Unknown"

    def generate_html_report(self, write_file):

        html = copy.deepcopy(ReportTemplate.get_body_template())

        row_one_html = "<div class='row'>"
        row_two_html = "<div class='row'>"

        tiny = [{"label": "Tests Executed:", "value": str(self.test_totals["total"]),
                 "tooltip": "Absolute # of tests executed.<br>May not match with the # of entries in the table "
                            "because parameterized tests are nested in the table."},
                {"label": "Passing Rate:", "value": "{:0.2f}%".format(float(self.test_totals[TestCategory.SUCCESS]) /
                                                                      float(self.test_totals["total"]) * 100)
                if self.test_totals[TestCategory.SUCCESS] > 0 else "0%", "tooltip": None},
                {"label": "Runtime:", "value": time.strftime('%Hh:%Mm:%Ss', time.gmtime(self.runtime)),
                 "tooltip": "Absolute time that it took to run all of the tests"},
                {"label": "Average Test Runtime:", "value": str(time.strftime('%Hh:%Mm:%Ss',
                                                                              time.gmtime(self.average_runtime))),
                 "tooltip": "Avg. time per test. This accounts only for the functions decorated with @test()"}]
        for card in tiny:
            row_one_html += ReportTemplate.get_tiny_card_template(card["label"], card["value"], card["tooltip"])

        row_two_html += ReportTemplate.get_health_of_features(self.__get_health_of_features())
        absolute_metrics = self.__get_absolute_results_dataset()
        row_two_html += ReportTemplate.get_absolute_results_template(absolute_metrics["data"],
                                                                     absolute_metrics["colors"])
        resource_data = None
        if self.monitoring_file is not None:
            # has to be before get_table data due to analysis call there
            resource_data = self.__get_resources_data()

        table_data = self.__get_table_data()
        row_two_html += ReportTemplate.get_suggestions(table_data["opportunities"])

        row_two_html += ReportTemplate.get_resource_chart_template(resource_data)
        row_one_html += ReportTemplate.get_tiny_card_template("Average CPU:", "{}%".format(self.__cpu_average))
        row_one_html += ReportTemplate.get_tiny_card_template("Average Mem:", "{}%".format(self.__mem_average))

        row_two_html += ReportTemplate.get_stacked_bar_results_template(
            features_data=self.__get_features_data(),
            components_data=self.__get_components_data(),
            team_data=self.__get_owner_data(),
            suites_data=self.__get_suites_data(),
            tags_data=self.__get_tags_data())

        # table_data = self.__get_table_data()
        row_two_html += ReportTemplate.get_table(table_data["table_data"])

        body = "{}</div>{}</div>{}".format(row_one_html, row_two_html, ReportTemplate.get_donation_options())
        html = html.format(body=body, database_lol=json.dumps(table_data["database_lol"]))
        with open(write_file, "w+") as output:
            output.write(html)

    def __get_resources_data(self):

        data = []
        cpu_samples = []
        mem_samples = []
        with open(self.monitoring_file, "r") as f:
            for line in f.readlines():
                line = line.replace("\n", "")
                li = line.split(",")
                cpu, mem = round(float(li[1]), 2), round(float(li[2]), 2)
                data.append({"date": li[0], "cpu": cpu, "mem": mem})
                cpu_samples.append(cpu)
                mem_samples.append(mem)
                self.analyzer.update_resources(cpu, mem)
        self.__cpu_average = Reporter.round(cpu_samples)
        self.__mem_average = Reporter.round(mem_samples)
        return data

    def __get_absolute_results_dataset(self):

        data = []
        colors = []
        for status, value in self.test_totals.items():
            if status != "total" and value > 0:
                data.append({"status": status, "value": value})
                colors.append(Color.MAPPING[status])

        return {"data": data, "colors": colors}

    def __get_health_of_features(self):

        data = []
        for feature, components in self.features.items():
            data.append({"full": 100, "category": feature if feature is not None else "Not Defined",
                         "value": Aggregator.percentage(components["_totals_"]["total"],
                                                        components["_totals_"][TestCategory.SUCCESS])})
        return data

    def __get_features_data(self):  # for the stacked bar
        data = []
        for feature, components in self.features.items():
            data_point = {"duration": Reporter.round(components["_totals_"]["performance"]),
                          "measure": feature if feature is not None else "Not Defined"}
            for status in TestCategory.ALL:
                data_point.update({status: components["_totals_"][status]})
            data.append(data_point)
        return data

    def __get_components_data(self):  # for the stacked bar
        data = []
        not_defined = {"measure": "Not Defined", "duration": []}
        for feature, components in self.features.items():
            for component, metrics in components.items():
                if component is None:  # Not defined components have to be aggregated from all features
                    not_defined["duration"] += metrics["performance"]
                    for status in TestCategory.ALL:
                        if status not in not_defined:
                            not_defined.update({status: metrics[status]})
                        else:
                            not_defined[status] += metrics[status]
                else:
                    if component != "_totals_":
                        data_point = {"duration": Reporter.round(metrics["performance"]), "measure": component}
                        for status in TestCategory.ALL:
                            data_point.update({status: metrics[status]})
                        data.append(data_point)
        if len(not_defined.keys()) > 2:
            not_defined["duration"] = Reporter.round(not_defined["duration"])
            data.append(not_defined)
        return data

    def __get_owner_data(self):  # for the stacked bar
        data = []
        for owner, metrics in self.owners.items():
            if owner != "_totals_":
                data_point = {"duration": Reporter.round(metrics["performance"]),
                              "measure": owner if owner is not None else "Not Defined"}
                for status in TestCategory.ALL:
                    data_point.update({status: metrics[status]})
                data.append(data_point)
        return data

    def __get_tags_data(self):  # for the stacked bar
        data = []
        for tag, metrics in self.tags.items():
            data_point = {"duration": Reporter.round(metrics["performance"]),
                          "measure": tag}
            for status in TestCategory.ALL:
                data_point.update({status: metrics[status]})
            data.append(data_point)
        return data

    def __get_suites_data(self):  # for the stacked bar
        data = []
        for suite, metrics in self.suites.items():
            if suite != "_totals_":
                data_point = {"duration": Reporter.round(metrics["performance"]),
                              "measure": suite}
                for status in TestCategory.ALL:
                    data_point.update({status: metrics[status]})
                data.append(data_point)
        return data

    def __get_table_data(self):  # for data table

        def convert_performance(_data):

            for _runtime in _data:
                _index = _data.index(_runtime)
                _data[_index] = "{:0.2f}s".format(_runtime)

        def convert_tracebacks(_data):

            for _traceback in _data:
                if _traceback is not None:
                    _index = _data.index(_traceback)
                    # _traceback = _traceback.replace("\n", "<br>").replace("    ", "&emsp;")
                    _data[_index] = _traceback

        def prioritize_status(_data):
            # tests are parameterized but table will show only parent test, thus have to give priority to one
            set(_data)
            if len(_data) == 1:
                return _data[0]
            else:
                for preferred_status in status_priority:
                    if preferred_status in _data:
                        return preferred_status

        def convert_suite_metrics(_data):
            new_suite_metrics = {}
            for _decorator in [DecoratorType.BEFORE_TEST, DecoratorType.AFTER_TEST,
                               DecoratorType.BEFORE_CLASS, DecoratorType.AFTER_CLASS]:
                med, avg, minimum, maximum, total = "N/A", "N/A", "N/A", "N/A", "N/A"
                if _data[_decorator]["performance"]:
                    med = "{:0.2f}s".format(median(_data[_decorator]["performance"]))
                    avg = "{:0.2f}s".format(mean(_data[_decorator]["performance"]))
                    minimum = "{:0.2f}s".format(min(_data[_decorator]["performance"]))
                    maximum = "{:0.2f}s".format(max(_data[_decorator]["performance"]))
                    total = "{}s".format(Reporter.total_up(_data[_decorator]["performance"]))
                executions = 0
                for traceback in _data[_decorator]["tracebacks"]:
                    if traceback != "N/A":
                        executions += 1
                failures = 0
                for exception in _data[_decorator]["exceptions"]:
                    if exception is not None:
                        failures += 1
                new_suite_metrics.update({_decorator: {"executions": executions, "failures": failures,
                                                       "median": med, "avg": avg, "total": total,
                                                       "minimum": minimum, "maximum": maximum}})
            return new_suite_metrics

        def get_copy(value):

            try:
                return copy.deepcopy(value)
            except:
                LogJunkie.error("Failed to deepcopy: {}. Metrics may be missing in the HTML report.".format(value))
                LogJunkie.error(traceback.format_exc())
                return None

        from statistics import median, mean

        status_priority = [TestCategory.CANCEL, TestCategory.IGNORE, TestCategory.ERROR,
                           TestCategory.FAIL, TestCategory.SKIP, TestCategory.SUCCESS]
        table_data = []
        database_lol = {"suites": {}, "tests": {}}
        executed_suites = self.aggregator.executed_suites
        suite_id = 0
        for suite in executed_suites:
            suite_id += 1
            suite_metrics = get_copy(suite.metrics.get_metrics())
            if suite_metrics is None:
                continue
            database_lol["suites"].update({suite_id: {"name": suite.get_class_name(),
                                                      "module": suite.get_class_module(),
                                                      "metrics": convert_suite_metrics(suite_metrics)}})
            for test in suite.get_test_objects():

                test_id = test.get_test_id()
                test_metrics = get_copy(test.metrics.get_metrics())
                if test_metrics is None:
                    continue
                duration, statuses = [], []

                component = test.get_component()
                component = "Not Defined" if component is None else component
                feature = suite.get_feature()
                feature = "Not Defined" if feature is None else feature
                assignee = test.get_owner()
                assignee = "Not Defined" if assignee is None else assignee

                test_name = test.get_function_name()
                suite_name = suite.get_class_name()

                for class_param, class_param_data in test_metrics.items():
                    for param, param_data in class_param_data.items():

                        self.analyzer.analyze(test_id=test_id,
                                              tracebacks=list(param_data["tracebacks"]),
                                              performance=list(param_data["performance"]))

                        duration += param_data["performance"]
                        statuses.append(param_data["status"])
                        # no value for exception objects in the HTML report, only will consume memory
                        for decorator in [DecoratorType.BEFORE_TEST, DecoratorType.AFTER_TEST]:
                            param_data[decorator].pop("exceptions")
                            convert_performance(param_data[decorator]["performance"])
                            convert_tracebacks(param_data[decorator]["tracebacks"])
                        param_data.pop("exceptions")
                        param_data.update({"params_total": Reporter.total_up(param_data["performance"])})
                        convert_performance(param_data["performance"])
                        convert_tracebacks(param_data["tracebacks"])

                duration = Reporter.total_up(duration)
                status = str(prioritize_status(statuses))

                table_data.append({"suite": suite_name, "test": test_name, "feature": feature, "component": component,
                                   "duration": duration, "status": status, "test_id": test_id, "suite_id": suite_id,
                                   "assignee": assignee})
                database_lol["tests"].update({test_id: {"name": test.get_function_name(),
                                                        "metrics": test_metrics,
                                                        "status": status}})
        return {"table_data": table_data, "database_lol": database_lol, "opportunities": self.analyzer.analysis}
