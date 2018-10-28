from test_junkie.runner import Runner
from tests.junkie_suites.BeforeClassExceptionSuite import BeforeClassExceptionSuite

runner = Runner(BeforeClassExceptionSuite)
runner.run()
results = runner.get_executed_suites()


def test_class_metrics():

    class_stats = results[0].metrics.get_metrics()
    assert class_stats["retry"] == 2
    assert class_stats["status"] == "fail"
    assert class_stats["runtime"] >= 0

    assert len(class_stats["afterClass"]["exceptions"]) == 0
    assert class_stats["afterClass"]["exceptions"] == []
    assert len(class_stats["afterClass"]["performance"]) == 0

    assert len(class_stats["beforeClass"]["exceptions"]) == 2
    for i in class_stats["beforeClass"]["exceptions"]:
        assert type(i) == Exception
    assert len(class_stats["beforeClass"]["performance"]) == 2

    assert len(class_stats["beforeTest"]["exceptions"]) == 0
    assert len(class_stats["beforeTest"]["performance"]) == 0

    assert len(class_stats["afterTest"]["performance"]) == 0
    assert len(class_stats["afterTest"]["exceptions"]) == 0


def test_test_metrics():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()["None"]["None"]
        for i in properties["exceptions"]:
            assert type(i) == Exception
        assert len(properties["exceptions"]) == 2
        assert len(properties["performance"]) == 2
        for i in properties["performance"]:
            assert i >= 0
        assert properties["status"] == "ignore"
        assert properties["retry"] == 2  # 2 not 4 (test x suite)
        assert properties["param"] is None
