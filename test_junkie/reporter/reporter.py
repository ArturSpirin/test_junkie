import time
from statistics import mean

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
        self.__processed_resources = {}

    def generate_html_report(self, write_file):

        with open(self.html_template, "r") as f:
            html = f.read()
            html = html.replace("{total_test_executed}", str(self.totals["total"]))
            html = html.replace("{absolute_passing_rate}", str(self.totals[TestCategory.SUCCESS] /
                                                               self.totals["total"] * 100)
                                if self.totals[TestCategory.SUCCESS] > 0 else 0)

            if self.monitoring_file is not None:
                html = html.replace("<span>Resource monitoring disabled</span>", "")
                cpu_data = self.__get_dataset_for_cpu_trend()
                html = html.replace("{cpu_labels}", str(cpu_data["labels"]))
                html = html.replace("{cpu_data}", str(cpu_data["data"]))
                html = html.replace("{average_cpu}", str(float("{0:.2f}".format(float(mean(cpu_data["samples"]))))))

                mem_data = self.__get_dataset_for_mem_trend()
                html = html.replace("{mem_labels}", str(mem_data["labels"]))
                html = html.replace("{mem_data}", str(mem_data["data"]))
                html = html.replace("{average_memory}", str(float("{0:.2f}".format(float(mean(mem_data["samples"]))))))
            else:
                html = html.replace("{average_cpu}", "Unknown ")
                html = html.replace("{average_memory}", "Unknown ")

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

    def __get_dataset_per_feature(self):

        labels = []
        datasets = []

        data = {TestCategory.SUCCESS: {"values": []},
                TestCategory.FAIL: {"values": []},
                TestCategory.ERROR: {"values": []},
                TestCategory.IGNORE: {"values": []},
                TestCategory.SKIP: {"values": []},
                TestCategory.CANCEL: {"values": []}}

        for feature, components in self.features.items():
            labels.append(feature if feature is not None else "Not Defined")
            for status, status_data in data.items():
                data[status]["values"].append(components["_totals_"][status])

        for status, status_data in data.items():
            datasets.append({"label": status,
                             "data": status_data["values"],
                             "backgroundColor": Reporter.__COLOR_MAPPING[status]})

        return {"labels": labels, "datasets": datasets}

    def __get_dataset_per_tag(self):

        labels = []
        datasets = []

        data = {TestCategory.SUCCESS: {"values": []},
                TestCategory.FAIL: {"values": []},
                TestCategory.ERROR: {"values": []},
                TestCategory.IGNORE: {"values": []},
                TestCategory.SKIP: {"values": []},
                TestCategory.CANCEL: {"values": []}}

        for tag, tag_data in self.tags.items():
            labels.append(tag)
            for status, status_data in data.items():
                data[status]["values"].append(tag_data[status])

        for status, status_data in data.items():
            datasets.append({"label": status,
                             "data": status_data["values"],
                             "backgroundColor": Reporter.__COLOR_MAPPING[status]})

        return {"labels": labels, "datasets": datasets}

    def __get_dataset_per_owner(self):

        labels = []
        datasets = []

        data = {TestCategory.SUCCESS: {"values": []},
                TestCategory.FAIL: {"values": []},
                TestCategory.ERROR: {"values": []},
                TestCategory.IGNORE: {"values": []},
                TestCategory.SKIP: {"values": []},
                TestCategory.CANCEL: {"values": []}}

        for owner, owner_data in self.owners.items():
            if owner == "_totals_":
                continue
            owner = owner if owner is not None else "Not Defined"
            labels.append(owner)
            for status, status_data in data.items():
                data[status]["values"].append(owner_data[status])

        for status, status_data in data.items():
            datasets.append({"label": status,
                             "data": status_data["values"],
                             "backgroundColor": Reporter.__COLOR_MAPPING[status]})

        return {"labels": labels, "datasets": datasets}

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

    def __get_dataset_for_cpu_trend(self):

        data = self.__process_resource_data()
        return {"labels": data["labels"],
                "data": data[1]["data"],
                "samples": data[1]["samples"]}

    def __get_dataset_for_mem_trend(self):

        data = self.__process_resource_data()
        return {"labels": data["labels"],
                "data": data[2]["data"],
                "samples": data[2]["samples"]}
