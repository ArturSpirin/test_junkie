from difflib import SequenceMatcher


class Analyzer:

    def __init__(self, monitoring_enabled=False, multi_threading_enabled=False):

        self.multi_threading_enabled = multi_threading_enabled
        self.__analysis = {"missing_definitions": {},
                           "traceback_insights": {},
                           "resources": {"monitoring_enabled": monitoring_enabled,
                                         "cpu": {"high": [], "medium": []},
                                         "mem": {"high": [], "medium": []}},
                           "time_lost_retrying": [],
                           "stable": True}

    def update_resources(self, cpu, mem):

        for level, value in {"high": 98, "medium": 70}.items():
            if cpu >= value:
                self.__analysis["resources"]["cpu"][level].append(cpu)
            if mem >= value:
                self.__analysis["resources"]["mem"][level].append(mem)

    def analyze(self, test_id, tracebacks, performance):
        """
        This function analyzes data for a specific test case against other known data from different test cases
        :param test_id: INT id of the test
        :param tracebacks: LIST of strings of the tracebacks
        :param performance: LIST of floats
        :return: None
        """
        index = 0
        for traceback in tracebacks:

            if index > 0:
                self.__analysis["time_lost_retrying"].append(performance[index])

            if traceback and traceback not in self.__analysis["traceback_insights"]:
                self.__analysis["stable"] = False
                self.__analysis["traceback_insights"].update({traceback: {"similar": [],
                                                                          "exact": [],
                                                                          "test_id": test_id}})
                for key in self.__analysis["traceback_insights"].keys():
                    if key != traceback:
                        if Analyzer.is_similar(traceback, key):
                            self.__analysis["traceback_insights"][key]["similar"].append(test_id)
            elif traceback and index == 0:
                self.__analysis["traceback_insights"][traceback]["exact"].append(test_id)

            index += 1

    @property
    def structured_analysis(self):
        """Returns insights as a list of dicts: {text, traceback, test_ids}.
        Use this instead of .analysis when rendering the new HTML report.
        """
        insights = []

        if self.__analysis["time_lost_retrying"]:
            total_sec = round(sum(self.__analysis["time_lost_retrying"]), 2)
            insights.append({
                "text": "Total of {} retries cost {} seconds.".format(
                    len(self.__analysis["time_lost_retrying"]), total_sec),
                "traceback": None, "test_ids": []
            })
        else:
            if self.__analysis["stable"]:
                insights.append({
                    "text": "All of your tests are stable and no time was lost on retries.",
                    "traceback": None, "test_ids": []
                })

        if self.__analysis["traceback_insights"]:
            if not self.__analysis["stable"]:
                insights.append({
                    "text": "There are {} unique tracebacks across all unsuccessful tests.".format(
                        len(self.__analysis["traceback_insights"])),
                    "traceback": None, "test_ids": []
                })
                ones_to_report_on = {}
                for tb_str, category in self.__analysis["traceback_insights"].items():
                    test_id = category["test_id"]
                    if test_id not in ones_to_report_on:
                        ones_to_report_on[test_id] = {"data": category, "traceback": tb_str}
                    elif len(category["similar"]) > len(ones_to_report_on[test_id]["data"]["similar"]):
                        ones_to_report_on[test_id] = {"data": category, "traceback": tb_str}

                for test_id, data in ones_to_report_on.items():
                    # only near-identical tracebacks are grouped - identical ones ("exact") are deliberately not
                    if len(data["data"]["similar"]) > 0:
                        affected_ids = [test_id] + list(data["data"]["similar"])
                        insights.append({
                            "text": "{} test failures share a similar traceback.".format(
                                len(data["data"]["similar"]) + 1),
                            "traceback": data["traceback"],
                            "test_ids": affected_ids
                        })

        if self.__analysis["resources"]["monitoring_enabled"]:
            if len(self.__analysis["resources"]["cpu"]["high"]) > 10:
                suffix = (
                    " and/or reducing thread allocation"
                    if self.multi_threading_enabled else ""
                )
                msg = ("CPU spiked {} times to critical levels during execution which may "
                       "have impacted test results. Consider closing background processes{}.".format(
                           len(self.__analysis["resources"]["cpu"]["high"]), suffix))
            else:
                if not self.multi_threading_enabled:
                    msg = "Consider enabling multi-threading to speed up test execution."
                else:
                    msg = "More CPU resources can be utilized; consider allocating more threads."
            insights.append({"text": msg, "traceback": None, "test_ids": []})

        return insights

    @staticmethod
    def is_similar(string_a, string_b):
        matcher = SequenceMatcher(None, string_a, string_b)
        return matcher.real_quick_ratio() >= 0.70 and matcher.quick_ratio() >= 0.70 and matcher.ratio() >= 0.70
