import copy
import json
import time
from test_junkie.constants import TestCategory, DecoratorType
from test_junkie.metrics import Aggregator
from test_junkie.reporter.reporter_template import ReportTemplate


class Reporter:

    COLOR_MAPPING = {TestCategory.SUCCESS: "#12d479",
                     TestCategory.FAIL: "#fcd75f",
                     TestCategory.ERROR: "#ff7651",
                     TestCategory.IGNORE: "#cce4eb",
                     TestCategory.SKIP: "#34bff5",
                     TestCategory.CANCEL: "#f19def"}

    @staticmethod
    def round(value):
        from statistics import mean
        if value:
            return str(float("{0:.2f}".format(float(mean(value)))))
        else:
            return "0"

    def __init__(self, monitoring_file, aggregator, runtime):

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

        tiny = [{"label": "Tests Executed:", "value": str(self.test_totals["total"])},
                {"label": "Passing Rate:", "value": "{:0.2f}%".format(float(self.test_totals[TestCategory.SUCCESS]) /
                                                                      float(self.test_totals["total"]) * 100)
                if self.test_totals[TestCategory.SUCCESS] > 0 else "0%"},
                {"label": "Runtime:", "value": time.strftime('%Hh:%Mm:%Ss', time.gmtime(self.runtime))},
                {"label": "Average Test Runtime:", "value": str(time.strftime('%Hh:%Mm:%Ss',
                                                                              time.gmtime(self.average_runtime)))}]
        for card in tiny:
            row_one_html += ReportTemplate.get_tiny_card_template(card["label"], card["value"])

        row_two_html += ReportTemplate.get_health_of_features(self.__get_health_of_features())
        absolute_metrics = self.__get_absolute_results_dataset()
        row_two_html += ReportTemplate.get_absolute_results_template(absolute_metrics["data"],
                                                                     absolute_metrics["colors"])
        row_two_html += ReportTemplate.get_suggestions(None)

        resource_data = None
        if self.monitoring_file is not None:
            resource_data = self.__get_resources_data()
        row_two_html += ReportTemplate.get_resource_chart_template(resource_data)
        row_one_html += ReportTemplate.get_tiny_card_template("Average CPU:", "{}%".format(self.__cpu_average))
        row_one_html += ReportTemplate.get_tiny_card_template("Average Mem:", "{}%".format(self.__mem_average))

        row_two_html += ReportTemplate.get_stacked_bar_results_template(
            features_data=self.__get_features_data(),
            components_data=self.__get_components_data(),
            team_data=self.__get_owner_data(),
            suites_data=self.__get_suites_data(),
            tags_data=self.__get_tags_data())

        table_data = self.__get_table_data()
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
        self.__cpu_average = Reporter.round(cpu_samples)
        self.__mem_average = Reporter.round(mem_samples)
        return data

    def __get_absolute_results_dataset(self):

        data = []
        colors = []
        for status, value in self.test_totals.items():
            if status != "total" and value > 0:
                data.append({"status": status, "value": value})
                colors.append(Reporter.COLOR_MAPPING[status])

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
        status_priority = [TestCategory.CANCEL, TestCategory.IGNORE, TestCategory.ERROR,
                           TestCategory.FAIL, TestCategory.SKIP, TestCategory.SUCCESS]
        table_data = []
        database_lol = {"suites": {}, "tests": {}}

        executed_suites = self.aggregator.executed_suites
        test_id = 0
        suite_id = 0
        for suite in executed_suites:
            suite_id += 1
            suite_metrics = copy.deepcopy(suite.metrics.get_metrics())

            # no value for exception objects in the HTML report, only will consume memory
            for decorator in [DecoratorType.BEFORE_TEST, DecoratorType.AFTER_TEST,
                              DecoratorType.BEFORE_CLASS, DecoratorType.AFTER_CLASS]:
                suite_metrics[decorator].pop("exceptions")

            database_lol["suites"].update({suite_id: {"name": suite.get_class_name(),
                                                      "module": suite.get_class_module(),
                                                      "metrics": suite_metrics}})
            for test in suite.get_test_objects():
                test_id += 1
                test_metrics = copy.deepcopy(test.metrics.get_metrics())
                duration = []
                statuses = []
                component = test.get_component()
                component = "Not Defined" if component is None else component
                feature = suite.get_feature()
                feature = "Not Defined" if feature is None else feature
                test_name = test.get_function_name()
                suite_name = suite.get_class_name()
                status = "unknown"  # Should never happen
                for class_param, class_param_data in test_metrics.items():
                    for param, param_data in class_param_data.items():
                        duration += param_data["performance"]
                        statuses.append(param_data["status"])

                        # no value for exception objects in the HTML report, only will consume memory
                        for decorator in [DecoratorType.BEFORE_TEST, DecoratorType.AFTER_TEST]:
                            param_data[decorator].pop("exceptions")
                        param_data.pop("exceptions")

                        for runtime in param_data["performance"]:
                            index = param_data["performance"].index(runtime)
                            test_metrics[class_param][param]["performance"][index] = "{:0.2f}s".format(runtime)
                        for traceback in param_data["tracebacks"]:
                            index = param_data["tracebacks"].index(traceback)
                            if traceback is not None:
                                traceback = traceback.replace("\n", "<br>").replace("    ", "&emsp;")
                                test_metrics[class_param][param]["tracebacks"][index] = traceback
                duration = Reporter.round(duration)
                set(statuses)
                if len(statuses) == 1:
                    status = statuses[0]
                else:  # tests are parameterized but table will show only parent test, thus have to give priority to one
                    for preferred_status in status_priority:
                        if preferred_status in statuses:
                            status = preferred_status
                            break
                table_data.append({"suite": suite_name, "test": test_name, "feature": feature, "component": component,
                                   "duration": duration, "status": status, "test_id": test_id, "suite_id": suite_id})
                database_lol["tests"].update({test_id: {"name": test.get_function_name(),
                                                        "metrics": test_metrics,
                                                        "status": status}})
        return {"table_data": table_data, "database_lol": database_lol}
