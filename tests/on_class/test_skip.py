import pprint

from test_junkie.runner import Runner
from tests.junkie_suites.SkipSuite import SkipSuite

runner = Runner(SkipSuite)
runner.run()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics():

    class_stats = results[0].metrics.get_metrics()
    assert class_stats["retry"] == 0
    assert class_stats["status"] == "skip"
    assert class_stats["runtime"] >= 0

    assert len(class_stats["afterClass"]["exceptions"]) == 0
    assert len(class_stats["afterClass"]["performance"]) == 0

    assert class_stats["beforeClass"]["exceptions"] == []
    assert len(class_stats["beforeClass"]["performance"]) == 0

    assert class_stats["beforeTest"]["exceptions"] == []
    assert len(class_stats["beforeTest"]["performance"]) == 0

    assert class_stats["afterTest"]["exceptions"] == []
    assert len(class_stats["afterTest"]["performance"]) == 0


def test_test_metrics2():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0
