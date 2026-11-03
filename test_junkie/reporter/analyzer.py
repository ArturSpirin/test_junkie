import re
from difflib import SequenceMatcher

# line numbers, ids, counts and addresses: what usually differs between two failures of the same kind
_VOLATILE = re.compile(r"0x[0-9a-fA-F]+|\d+")


def _exception_type(traceback):
    lines = traceback.strip().splitlines()
    return lines[-1].split(":", 1)[0].strip() if lines else ""


class Analyzer:

    # similar-traceback grouping: a new kind of traceback is compared with at most MAX_CANDIDATES groups, and with
    # none once the run has made MAX_COMPARISONS full comparisons. Raise them for more grouping on very large runs
    MAX_CANDIDATES = 10
    MAX_COMPARISONS = 2000

    def __init__(self, monitoring_enabled=False, multi_threading_enabled=False):

        self.multi_threading_enabled = multi_threading_enabled
        self.__groups = []  # {"traceback", "matcher", "type", "test_ids"}, in the order they were made
        self.__group_of = {}  # (masked traceback, exception type) -> group
        self.__comparisons = 0
        self.__not_compared = 0
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
                self.__analysis["traceback_insights"].update({traceback: {"exact": [],
                                                                          "test_id": test_id}})
                self.__group(test_id, traceback)
            elif traceback and index == 0:
                self.__analysis["traceback_insights"][traceback]["exact"].append(test_id)

            index += 1

    def __group(self, test_id, traceback):
        """
        Puts a new distinct traceback in the first group it is similar to (is_similar against the group's first
        traceback), or in a new group. Tracebacks that differ only in numbers, with the same exception type, join
        without a comparison
        """
        exception_type = _exception_type(traceback)
        key = (_VOLATILE.sub("#", traceback), exception_type)
        group = self.__group_of.get(key)
        if group is None:
            group = self.__most_similar_group(traceback, exception_type)
        if group is None:
            group = {"traceback": traceback, "matcher": None, "type": exception_type, "test_ids": []}
            self.__groups.append(group)
        self.__group_of.setdefault(key, group)
        if test_id not in group["test_ids"]:
            group["test_ids"].append(test_id)

    def __most_similar_group(self, traceback, exception_type):
        if not self.__groups:
            return None
        if self.__comparisons >= self.MAX_COMPARISONS:
            self.__not_compared += 1
            return None
        # same exception type first, then the biggest groups; sorted() keeps creation order among equals
        candidates = sorted(self.__groups, key=lambda g: (g["type"] != exception_type, -len(g["test_ids"])))
        for group in candidates[:self.MAX_CANDIDATES]:
            if self.__comparisons >= self.MAX_COMPARISONS:
                self.__not_compared += 1
                return None
            if group["matcher"] is None:  # b stays the representative: difflib indexes it once, not per comparison
                group["matcher"] = SequenceMatcher(None, "", group["traceback"])
            matcher = group["matcher"]
            matcher.set_seq1(traceback)
            if matcher.real_quick_ratio() >= 0.70 and matcher.quick_ratio() >= 0.70:
                self.__comparisons += 1
                if matcher.ratio() >= 0.70:
                    return group
        return None

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
                # only near-identical tracebacks are grouped - identical ones ("exact") are deliberately not
                for group in self.__groups:
                    if len(group["test_ids"]) > 1:
                        insights.append({
                            "text": "{} test failures share a similar traceback.".format(len(group["test_ids"])),
                            "traceback": group["traceback"],
                            "test_ids": list(group["test_ids"])
                        })
                if self.__not_compared:
                    insights.append({
                        "text": "Similar-traceback grouping stopped after {} comparisons; {} tracebacks were not "
                                "compared.".format(self.__comparisons, self.__not_compared),
                        "traceback": None, "test_ids": []
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
