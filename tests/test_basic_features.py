from test_junkie.runner import Runner
from tests.junkie_suites.BasicSuite import BasicSuite

runner = Runner(BasicSuite)
runner.run()
results = runner.get_executed_suites()
tests = results[0].get_test_objects()


def test_class_stats():

    class_stats = results[0].metrics.get_metrics()
    assert class_stats["retry"] == 1
    assert class_stats["status"] == "fail"
    assert class_stats["runtime"] >= 0

    for i in ["afterClass", "beforeClass"]:
        assert len(class_stats[i]["exceptions"]) == 1
        assert class_stats[i]["exceptions"] == [None]
        assert len(class_stats[i]["performance"]) == 1

    assert len(class_stats["beforeTest"]["exceptions"]) == 8
    for i in class_stats["beforeTest"]["exceptions"]:
        assert i is None
    assert len(class_stats["beforeTest"]["performance"]) == 8
    for i in class_stats["beforeTest"]["performance"]:
        assert i >= 0

    assert len(class_stats["afterTest"]["performance"]) == 4
    for i in class_stats["afterTest"]["performance"]:
        assert i >= 0
    assert len(class_stats["afterTest"]["exceptions"]) == 4
    for i in class_stats["afterTest"]["exceptions"]:
        assert i is None


def test_failure():

    tested = False
    for test in tests:
        if test.get_function_name() == "failure":
            properties = test.metrics.get_metrics()["None"]["None"]
            assert isinstance(properties["exceptions"][0], AssertionError)
            assert len(properties["exceptions"]) == 1
            assert len(properties["performance"]) == 1
            assert properties["performance"][0] >= 0
            assert properties["status"] == "fail"
            assert properties["retry"] == 1
            assert properties["param"] is None
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_error():

    tested = False
    for test in tests:
        if test.get_function_name() == "error":
            properties = test.metrics.get_metrics()["None"]["None"]
            # assert Exception in properties["exceptions"]
            assert isinstance(properties["exceptions"][0], Exception)
            assert len(properties["exceptions"]) == 1
            assert len(properties["performance"]) == 1
            assert properties["performance"][0] >= 0
            assert properties["status"] == "error"
            assert properties["retry"] == 1
            assert properties["param"] is None
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_skip():

    tested = False
    for test in tests:
        if test.get_function_name() == "skip":
            properties = test.metrics.get_metrics()["None"]["None"]
            assert None in properties["exceptions"]
            assert len(properties["exceptions"]) == 1
            assert len(properties["performance"]) == 1
            assert properties["performance"][0] >= 0
            assert properties["status"] == "skip"
            assert properties["retry"] == 1
            assert properties["param"] is None
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_skip_function():

    tested = False
    for test in tests:
        if test.get_function_name() == "skip_function":
            properties = test.metrics.get_metrics()["None"]["None"]
            assert None in properties["exceptions"]
            assert len(properties["exceptions"]) == 1
            assert len(properties["performance"]) == 1
            assert properties["performance"][0] >= 0
            assert properties["status"] == "skip"
            assert properties["retry"] == 1
            assert properties["param"] is None
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry":
            properties = test.metrics.get_metrics()["None"]["None"]
            for assertion in properties["exceptions"]:
                assert isinstance(assertion, AssertionError)
            assert len(properties["exceptions"]) == 2
            assert len(properties["performance"]) == 2
            assert properties["performance"][0] >= 0
            assert properties["status"] == "fail"
            assert properties["retry"] == 2
            assert properties["param"] is None
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_parameters():

    tested = False
    for test in tests:
        if test.get_function_name() == "parameters":
            properties = test.metrics.get_metrics()["None"]
            for param, metrics in properties.items():
                assert None in metrics["exceptions"]
                assert len(metrics["exceptions"]) == 1
                assert len(metrics["performance"]) == 1
                assert metrics["performance"][0] >= 0
                assert metrics["status"] == "success"
                assert metrics["retry"] == 1
                assert str(metrics["param"]) == param
            tested = True
    if not tested:
        raise Exception("Test did not run")
