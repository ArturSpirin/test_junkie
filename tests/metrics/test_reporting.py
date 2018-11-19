import pprint, sys
import time

sys.path.insert(1, __file__.split("tests")[0])
from test_junkie.runner import Runner
from tests.junkie_suites.FeatureAggregations import LoginSessions, Login, Dashboard

f = __file__.replace("test_reporting.py", "test_{}".format(int(time.time())))
html = "{}.html".format(f)
xml = "{}.xml".format(f)
runner = Runner([Login, LoginSessions, Dashboard],
                monitor_resources=True, html_report=html, xml_report=xml)
runner_metrics = runner.run()
results = runner.get_executed_suites()
tests = results[0].get_test_objects()
pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())
