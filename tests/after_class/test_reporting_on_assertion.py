import pprint

from test_junkie.runner import Runner
from tests.junkie_suites.AfterClassAssertionSuite import AfterClassAssertionSuite

runner = Runner(AfterClassAssertionSuite)
runner.run()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics():

    class_stats = results[0].metrics.get_metrics()
    assert class_stats["retry"] == 1
    assert class_stats["status"] == "success"
    assert class_stats["runtime"] >= 0

    assert len(class_stats["afterClass"]["exceptions"]) == 1
    for i in class_stats["afterClass"]["exceptions"]:
        assert type(i) == AssertionError
    assert len(class_stats["afterClass"]["performance"]) == 1
    for i in class_stats["afterClass"]["performance"]:
        assert i >= 0

    assert class_stats["beforeClass"]["exceptions"] == [None]
    assert len(class_stats["beforeClass"]["performance"]) == 1

    # There are not functions decorated with before test for this suite
    assert class_stats["beforeTest"]["exceptions"] == []
    assert len(class_stats["beforeTest"]["performance"]) == 0

    # There are not functions decorated with after test for this suite
    assert class_stats["afterTest"]["exceptions"] == []
    assert len(class_stats["afterTest"]["performance"]) == 0


def test_test_metrics():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()["None"]["None"]
        assert properties["exceptions"] == [None]
        assert len(properties["performance"]) == 1
        for i in properties["performance"]:
            assert i >= 0
        assert properties["status"] == "success"
        assert properties["retry"] == 1
        assert properties["param"] is None
