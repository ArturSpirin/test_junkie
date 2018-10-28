import pprint
import threading

from test_junkie.runner import Runner
from tests.junkie_suites.CancelSuite import CancelSuite

runner = Runner(CancelSuite)
thread = threading.Thread(target=runner.run, args=())
thread.start()
runner.cancel()
thread.join()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics():

    class_stats = results[0].metrics.get_metrics()
    assert class_stats["retry"] == 1
    assert class_stats["status"] == "success"
    assert class_stats["runtime"] >= 2

    assert class_stats["afterClass"]["exceptions"] == [None]
    assert len(class_stats["afterClass"]["performance"]) == 1

    assert class_stats["beforeClass"]["exceptions"] == [None]
    assert len(class_stats["beforeClass"]["performance"]) == 1
    assert class_stats["beforeClass"]["performance"][0] > 2

    assert class_stats["beforeTest"]["exceptions"] == []
    assert class_stats["beforeTest"]["performance"] == []

    assert class_stats["afterTest"]["exceptions"] == []
    assert class_stats["afterTest"]["performance"] == []


def test_test_metrics():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()["None"]["None"]
        assert properties["exceptions"] == [None]
        assert len(properties["performance"]) == 1
        for i in properties["performance"]:
            assert i >= 0
        assert properties["status"] == "cancel"
        assert properties["retry"] == 1
        assert properties["param"] is None
