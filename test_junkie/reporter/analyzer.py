from difflib import SequenceMatcher


class Analyzer:

    def __init__(self):

        self.__analysis = {"missing_definitions": {},
                           "insights": {},
                           "time_lost_retrying": []}

    def analyze(self, test_id, tracebacks, performance):

        index = 0
        for traceback in tracebacks:

            if index > 0:
                self.__analysis["time_lost_retrying"].append(performance[index])

            if traceback and traceback not in self.__analysis["insights"]:
                self.__analysis["insights"].update({traceback: {"similar": [], "exact": []}})
                for key in self.__analysis["insights"].keys():
                    if key != traceback:
                        if Analyzer.is_similar(traceback, key):
                            self.__analysis["insights"][key]["similar"].append(test_id)
            elif traceback and index == 0:
                self.__analysis["insights"][traceback]["exact"].append(test_id)

            index += 1

    @property
    def analysis(self):
        analysis = []

        if self.__analysis["time_lost_retrying"]:
            from test_junkie.reporter.html_reporter import Reporter
            analysis.append("Total of {retries} retries cost you {seconds} seconds"
                            .format(retries=len(self.__analysis["time_lost_retrying"]),
                                    seconds=Reporter.total_up(self.__analysis["time_lost_retrying"])))
        else:
            analysis.append("All of your tests are stable and thus no time was lost on retries")

        if self.__analysis["insights"]:
            analysis.append("There are {tracebacks} unique tracebacks across all of the unsuccessful tests"
                            .format(tracebacks=len(self.__analysis["insights"])))
        return analysis

    @staticmethod
    def is_similar(string_a, string_b):
        if SequenceMatcher(None, string_a, string_b).ratio() >= 0.70:
            return True
        return False

    def is_missing_definitions(self, data):

        pass
