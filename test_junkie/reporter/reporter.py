import copy
import time
from test_junkie.constants import TestCategory
from test_junkie.reporter.reporter_template import ReportTemplate


class Reporter:

    __COLOR_MAPPING = {TestCategory.SUCCESS: "#D6E9C6",
                       TestCategory.FAIL: "#fcd75f",
                       TestCategory.ERROR: "#ff7651",
                       TestCategory.IGNORE: "#ebd3cc",
                       TestCategory.SKIP: "#cce4eb",
                       TestCategory.CANCEL: "#ebcce9"}

    def __init__(self, monitoring_file, aggregator, runtime):

        self.monitoring_file = monitoring_file
        self.features = aggregator.get_report_by_features()
        self.tags = aggregator.get_report_by_tags()
        self.totals = aggregator.get_basic_report()
        self.owners = aggregator.get_report_by_owner()
        self.runtime = runtime
        self.average_runtime = aggregator.get_average_test_runtime()
        self.__processed_resources = {}

    def generate_html_report(self, write_file):

        def __round(value):
            from statistics import mean
            if value:
                return str(float("{0:.2f}".format(float(mean(value)))))
            else:
                return "0"

        html = copy.deepcopy(ReportTemplate.get_body_template())

        row_one_html = "<div class='row'>"
        row_two_html = "<div class='row'>"

        tiny = [{"label": "Tests Executed:", "value": str(self.totals["total"])},
                {"label": "Passing Rate:", "value": "{:0.2f}%".format(float(self.totals[TestCategory.SUCCESS]) /
                                                                     float(self.totals["total"]) * 100)
                if self.totals[TestCategory.SUCCESS] > 0 else "0"},
                {"label": "Runtime:", "value": time.strftime('%Hh:%Mm:%Ss', time.gmtime(self.runtime))},
                {"label": "Average Test Runtime:", "value": str(time.strftime('%Hh:%Mm:%Ss',
                                                                              time.gmtime(self.average_runtime)))}]
        for card in tiny:
            row_one_html += ReportTemplate.get_tiny_card_template(card["label"], card["value"])

        for resource in [{"key": "cpu", "id": 1}, {"key": "mem", "id": 2}]:
            if self.monitoring_file is not None:
                resource_data = self.__get_source_dataset(resource.get("id"))
                avg, data, labels = "{}%".format(__round(resource_data["samples"])), \
                                    str(resource_data["data"]), \
                                    str(resource_data["labels"])
            else:
                avg, data, labels = "Unknown", "", ""
            row_two_html += ReportTemplate.get_resource_chart_template(resource.get("key"), data, labels)
            row_one_html += ReportTemplate.get_tiny_card_template("Average {}:".format(resource.get("key")), avg)

        if self.monitoring_file is not None:
            row_two_html = row_two_html.replace("<span>Resource monitoring disabled</span>", "")

        row_two_html += ReportTemplate.get_absolute_results_template(str(self.__get_absolute_results_dataset()))
        cards = [{"label": "Feature", "value": self.__get_dataset_per_feature(), "id": "feature"},
                 {"label": "Tag", "value": self.__get_dataset_per_tag(), "id": "tag"},
                 {"label": "Owner", "value": self.__get_dataset_per_owner(), "id": "owner"}]

        for card in cards:
            row_two_html += ReportTemplate.get_stacked_bar_results_template(
                card["id"], str(card["value"]), card["label"])

        body = "{}</div>{}</div>".format(row_one_html, row_two_html)
        html = html.format(body=body)
        with open(write_file, "w+") as output:
            output.write(html)

    @staticmethod
    def __get_template():

        return {TestCategory.SUCCESS: {"values": []},
                TestCategory.FAIL: {"values": []},
                TestCategory.ERROR: {"values": []},
                TestCategory.IGNORE: {"values": []},
                TestCategory.SKIP: {"values": []},
                TestCategory.CANCEL: {"values": []}}

    @staticmethod
    def __get_datasets(data):
        datasets = []
        for status, status_data in data.items():
            datasets.append({"label": status,
                             "data": status_data["values"],
                             "backgroundColor": Reporter.__COLOR_MAPPING[status]})
        return datasets

    def __get_dataset_per_feature(self):

        labels = []
        data = Reporter.__get_template()
        for feature, components in self.features.items():
            labels.append(feature if feature is not None else "Not Defined")
            for status, status_data in data.items():
                data[status]["values"].append(components["_totals_"][status])
        return {"labels": labels, "datasets": Reporter.__get_datasets(data)}

    def __get_dataset_per_tag(self):

        labels = []
        data = Reporter.__get_template()
        for tag, tag_data in self.tags.items():
            labels.append(tag)
            for status, status_data in data.items():
                data[status]["values"].append(tag_data[status])
        return {"labels": labels, "datasets": Reporter.__get_datasets(data)}

    def __get_dataset_per_owner(self):

        labels = []
        data = Reporter.__get_template()
        for owner, owner_data in self.owners.items():
            if owner == "_totals_":
                continue
            owner = owner if owner is not None else "Not Defined"
            labels.append(owner)
            for status, status_data in data.items():
                data[status]["values"].append(owner_data[status])
        return {"labels": labels, "datasets": Reporter.__get_datasets(data)}

    def __get_dataset_per_suite(self):

        pass

    def __get_absolute_results_dataset(self):

        data = []
        colors = []
        labels = []

        for status, value in self.totals.items():
            if status != "total":
                labels.append(status)
                colors.append(Reporter.__COLOR_MAPPING[status])
                data.append(value)

        return {"datasets": [{"data": data, "backgroundColor": colors}], "labels": labels}

    def __process_resource_data(self):

        cpu = 1
        mem = 2

        if not self.__processed_resources:
            labels = []
            cpu_data = {"fill": 1, "label": "Usage", "data": [], "lineTension": 0,
                        "borderColor": "#fe8b36", "backgroundColor": "#fe8b36"}
            cpu_samples = []

            mem_data = {"fill": 1, "label": "Usage", "data": [], "lineTension": 0,
                        "borderColor": "#fe8b36", "backgroundColor": "#fe8b36"}
            mem_samples = []
            with open(self.monitoring_file, "r") as f:
                for line in f.readlines():
                    line = line.replace("\n", "")
                    li = line.split(",")
                    labels.append(li[0])

                    cpu_data["data"].append(li[cpu])
                    cpu_samples.append(round(float(li[cpu]), 2))

                    mem_data["data"].append(li[mem])
                    mem_samples.append(round(float(li[mem]), 2))
            self.__processed_resources.update({cpu: {"data": cpu_data,
                                                     "samples": cpu_samples},
                                               mem: {"data": mem_data,
                                                     "samples": mem_samples},
                                               "labels": labels})
        return self.__processed_resources

    def __get_source_dataset(self, index):
        """
        Will parse out the resource data
        :param index: INT
        :return: DICT
        """
        data = self.__process_resource_data()
        return {"labels": data["labels"],
                "data": data[index]["data"],
                "samples": data[index]["samples"]}
