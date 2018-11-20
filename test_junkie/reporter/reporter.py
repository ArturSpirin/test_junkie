import time
from test_junkie.constants import TestCategory


class Reporter:

    __COLOR_MAPPING = {TestCategory.SUCCESS: "#D6E9C6",
                       TestCategory.FAIL: "#FAEBCC",
                       TestCategory.ERROR: "#ebcccc",
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
        self.html_template = __file__.replace("reporter.py", "report_template.html")
        if self.html_template.endswith("c"):
            self.html_template = self.html_template.split("c")[0]
        self.__processed_resources = {}

    def generate_html_report(self, write_file):

        def __round(value):
            return str(float("{0:.2f}".format(float(mean(value)))))

        with open(self.html_template, "r") as f:
            html = f.read()
            html = html.replace("{total_test_executed}", str(self.totals["total"]))
            html = html.replace("{absolute_passing_rate}", str(self.totals[TestCategory.SUCCESS] /
                                                               self.totals["total"] * 100)
                                if self.totals[TestCategory.SUCCESS] > 0 else 0)

            if self.monitoring_file is not None:
                from statistics import mean
                html = html.replace("<span>Resource monitoring disabled</span>", "")
                for resource in [{"key": "cpu", "id": 1}, {"key": "mem", "id": 2}]:
                    resource_data = self.__get_source_dataset(resource.get("id"))
                    html = html.replace("{{{key}_labels}}".format(key=resource.get("key")),
                                        str(resource_data["labels"]))
                    html = html.replace("{{{key}_data}}".format(key=resource.get("key")),
                                        str(resource_data["data"]))
                    html = html.replace("{{average_{key}}}".format(key=resource.get("key")),
                                        __round(resource_data["samples"]))
            else:
                html = html.replace("{average_cpu}", "Unknown ")
                html = html.replace("{average_mem}", "Unknown ")

            html = html.replace("{absolute_data}", str(self.__get_absolute_results_dataset()))

            html = html.replace("{features_data}", str(self.__get_dataset_per_feature()))
            html = html.replace("{tags_data}", str(self.__get_dataset_per_tag()))
            html = html.replace("{owners_data}", str(self.__get_dataset_per_owner()))

            runtime = time.strftime('%Hh:%Mm:%Ss', time.gmtime(self.runtime))
            html = html.replace("{total_runtime}", str(runtime))
            average_runtime = time.strftime('%Hh:%Mm:%Ss', time.gmtime(self.average_runtime))
            html = html.replace("{average_test_runtime}", str(average_runtime))

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
                    li = line.split(" ")
                    labels.append(float(li[0]))

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
