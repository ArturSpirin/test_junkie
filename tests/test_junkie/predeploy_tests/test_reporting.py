import os
import time

from test_junkie.decorators import Suite, test
from test_junkie.runner import Runner
from tests.junkie_suites.Reporting import Login, LoginSessions, Dashboard


@Suite()
class ReportingTestSuite:

    @test()
    def reporting(self):
        base = os.path.join(os.path.dirname(__file__), "test_{}".format(int(time.time())))
        html = "{}.html".format(base)
        xml = "{}.xml".format(base)
        runner = Runner([Login, LoginSessions, Dashboard],
                        monitor_resources=True, html_report=html, xml_report=xml)
        runner.run()

        suites = runner.get_executed_suites()
        for suite in suites:
            suite.metrics.get_average_performance_of_after_class()
            suite.metrics.get_average_performance_of_before_class()
            suite.metrics.get_average_performance_of_after_test()
            suite.metrics.get_average_performance_of_before_test()
