import pprint
import threading
import sys
sys.path.insert(1, __file__.split("tests")[0])
from tests.QualityManager import QualityManager
from test_junkie.runner import Runner
from tests.junkie_suites.CancelSuite import CancelSuite

runner = Runner([CancelSuite])
thread = threading.Thread(target=runner.run, args=())
runner.cancel()
thread.start()
thread.join()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_retry_count=0,
                                       expected_status="cancel")


def test_test_metrics():

    # Runner.cancel() came before the suite started: its tests are listed as cancelled, once each, as Ctrl+C lists
    # them (they used to have no record, so the JSON/HTML totals left them out while the console counted them)
    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert list(properties) == ["None"] and list(properties["None"]) == ["None"], properties
        assert properties["None"]["None"]["status"] == "cancel" and properties["None"]["None"]["retry"] == 1
