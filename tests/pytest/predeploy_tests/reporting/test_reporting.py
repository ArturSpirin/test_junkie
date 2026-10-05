import sys
import time

sys.path.insert(1, __file__.split("tests")[0])

from test_junkie.runner import Runner
from tests.junkie_suites.Reporting import LoginSessions, Login, Dashboard


def test_reporting():
    f = __file__.replace("test_reporting.py", "test_{}".format(int(time.time())))
    html = "{}.html".format(f)
    xml = "{}.xml".format(f)
    runner = Runner([Login, LoginSessions, Dashboard],
                    monitor_resources=True, html_report=html, xml_report=xml)
    runner.run()

    suites = runner.get_executed_suites()
    for suite in suites:
        suite.metrics.get_average_performance_of_after_class()
        suite.metrics.get_average_performance_of_before_class()
        suite.metrics.get_average_performance_of_after_test()
        suite.metrics.get_average_performance_of_before_test()
