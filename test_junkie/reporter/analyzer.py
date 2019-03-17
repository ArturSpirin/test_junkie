from difflib import SequenceMatcher
from html import escape
from test_junkie.constants import DocumentationLinks


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
    def analysis(self):
        """
        This function does a final analysis across the dataset at the time and returns usable HTML for the report
        :return: LIST of STRINGs with HTML ready to go
        """
        analysis = []

        # analyzing retries
        retry_link = "<a ref='noopener' target='_blank' href='{}'>retries <i class='fas fa-external-link-alt'></i></a>"\
                     .format(DocumentationLinks.RETRY)
        if self.__analysis["time_lost_retrying"]:
            from test_junkie.reporter.html_reporter import Reporter
            analysis.append("Total of {retries} {link} cost you {seconds} seconds."
                            .format(retries=len(self.__analysis["time_lost_retrying"]),
                                    seconds=Reporter.total_up(self.__analysis["time_lost_retrying"]),
                                    link=retry_link))
        else:
            if self.__analysis["stable"]:
                analysis.append("All of your tests are stable and thus no time was lost on {link}."
                                .format(link=retry_link))

        # analyzing tracebacks
        if self.__analysis["traceback_insights"]:
            if not self.__analysis["stable"]:
                analysis.append("There are {tracebacks} unique tracebacks across all of the unsuccessful tests."
                                .format(tracebacks=len(self.__analysis["traceback_insights"])))
                ones_to_report_on = {}
                for traceback, category in self.__analysis["traceback_insights"].items():
                    # tb = traceback.replace("\n", "<br>").replace("    ", "&emsp;")
                    test_id = category["test_id"]
                    if test_id not in ones_to_report_on:
                        ones_to_report_on.update({test_id: {"data": category, "traceback": traceback}})
                    elif len(category["similar"]) > len(ones_to_report_on[test_id]["data"]["similar"]):
                        ones_to_report_on.update({test_id: {"data": category, "traceback": traceback}})

                if ones_to_report_on:
                    for test_id, data in ones_to_report_on.items():
                        if len(data["data"]["similar"]) > 0:
                            tb = escape(data["traceback"], quote=True)

                            analysis.append(
                                "{similar_count} test failures due to a similar "
                                "<span data-html='true' data-tooltip='<xmp>{traceback}</xmp>' "
                                "class='tooltipped traceback-tooltip'>"
                                "&nbsp;traceback <i class='fas fa-project-diagram'></i>&nbsp;</span>"
                                .format(traceback=tb, similar_count=len(data["data"]["similar"]) + 1))

        # analyzing CPU/MEM
        if self.__analysis["resources"]["monitoring_enabled"]:
            link = "See documentation for <a ref='noopener' target='_blank' href='{}'>Parallel Execution " \
                   "<i class='fas fa-external-link-alt'></i></a>".format(DocumentationLinks.THREADING)
            if len(self.__analysis["resources"]["cpu"]["high"]) > 10:
                msg = "CPU has spiked {} times to critical levels over the course of test execution which may have "\
                      "impacted some of the tests. You may want to shut down any unnecessary background processes{}"\
                      .format(len(self.__analysis["resources"]["cpu"]["high"]),
                              "and/or reduce thread allocation. {}".format(link)
                              if self.multi_threading_enabled else ".")
                analysis.append(msg)
            else:
                if not self.multi_threading_enabled:
                    msg = "Consider enabling multi-threading."
                else:
                    msg = "More of the resources can be utilized, consider allocating more " \
                          "threads. {}".format(link)
                analysis.append(msg)

        return analysis

    @staticmethod
    def is_similar(string_a, string_b):
        if SequenceMatcher(None, string_a, string_b).ratio() >= 0.70:
            return True
        return False

    def is_missing_definitions(self, data):

        pass
