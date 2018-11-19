import pprint

from test_junkie.runner import Runner
from tests.junkie_suites.FeatureAggregations import LoginSessions, Login, Dashboard

html = "{}.html".format(__file__)
xml = "{}.xml".format(__file__)
runner = Runner([Login, LoginSessions, Dashboard],
                monitor_resources=True, html_report=html, xml_report=xml)
runner_metrics = runner.run()
results = runner.get_executed_suites()
tests = results[0].get_test_objects()
pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())
