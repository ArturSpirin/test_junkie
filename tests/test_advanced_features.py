import pprint
import sys
sys.path.insert(1, __file__.split("tests")[0])
from test_junkie.debugger import LogJunkie
LogJunkie.enable_logging(10)

from test_junkie.runner import Runner
from tests.junkie_suites.AdvancedSuite import AdvancedSuite

runner = Runner(AdvancedSuite)
runner.run(suite_multithreading=True, suite_multithreading_limit=5,
           test_multithreading=True, test_multithreading_limit=5,
           tag_config={"run_on_match_all": ["critical", "v2"],
                       "run_on_match_any": ["critical2"],
                       "skip_on_match_all": ["skip", "v2"],
                       "skip_on_match_any": ["trivial"]})
results = runner.get_executed_suites()
tests = results[0].get_test_objects()

pprint.pprint(results[0].metrics.get_metrics())
for test in tests:
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_stats():

    class_stats = results[0].metrics.get_metrics()
    assert class_stats["retry"] == 2
    assert class_stats["status"] == "fail"
    assert class_stats["runtime"] >= 0

    for i in ["afterClass", "beforeClass"]:
        for l in class_stats[i]["exceptions"]:  # Should be no exceptions in class level decorators
            assert l is None
        assert len(class_stats[i]["exceptions"]) == 4
        assert len(class_stats[i]["performance"]) == 4
        for l in class_stats[i]["performance"]:
            assert l >= 0

    assert len(class_stats["beforeTest"]["exceptions"]) == 47
    for i in class_stats["beforeTest"]["exceptions"]:
        assert i is None
    assert len(class_stats["beforeTest"]["performance"]) == 47
    for i in class_stats["beforeTest"]["performance"]:
        assert i >= 0

    assert len(class_stats["afterTest"]["performance"]) == 19
    for i in class_stats["afterTest"]["performance"]:
        assert i >= 0
    assert len(class_stats["afterTest"]["exceptions"]) == 19
    for i in class_stats["afterTest"]["exceptions"]:
        assert i is None


def test_no_retry():

    tested = False
    for test in tests:
        if test.get_function_name() == "no_retry":
            for class_param, class_data in test.metrics.get_metrics().items():
                for test_param, properties in class_data.items():
                    assert properties["exceptions"] == [None]
                    assert len(properties["performance"]) == 1
                    assert properties["performance"][0] >= 0
                    assert properties["status"] == "success"
                    assert properties["retry"] == 1
                    assert properties["param"] is not None
                    assert properties["class_param"] is not None
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_no_retry2():

    tested = False
    for test in tests:
        if test.get_function_name() == "no_retry2":
            for class_param, class_data in test.metrics.get_metrics().items():
                for test_param, properties in class_data.items():
                    assert properties["exceptions"] == [None]
                    assert len(properties["performance"]) == 1
                    assert properties["performance"][0] >= 0
                    assert properties["status"] == "success"
                    assert properties["retry"] == 1
                    assert properties["param"] is not None
                    assert properties["class_param"] is not None
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_no_retry3():

    tested = False
    for test in tests:
        if test.get_function_name() == "no_retry3":
            for class_param, class_data in test.metrics.get_metrics().items():
                for test_param, properties in class_data.items():
                    assert properties["exceptions"] == [None]
                    assert len(properties["performance"]) == 1
                    assert properties["performance"][0] >= 0
                    assert properties["status"] == "success"
                    assert properties["retry"] == 1
                    assert properties["param"] is not None
                    assert properties["class_param"] is not None
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry":
            for class_param, class_data in test.metrics.get_metrics().items():
                for test_param, properties in class_data.items():
                    for i in properties["exceptions"]:
                        assert type(i) == AssertionError
                        assert str(i.with_traceback(None)) == "Expected Assertion Error"
                    assert len(properties["performance"]) == 4
                    assert properties["performance"][0] >= 0
                    assert properties["status"] == "fail"
                    assert properties["retry"] == 4
                    assert properties["param"] is None
                    assert properties["class_param"] is not None
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry2():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry2":
            for class_param, class_data in test.metrics.get_metrics().items():
                for test_param, properties in class_data.items():
                    assert properties["exceptions"] == [None, None, None, None]
                    assert len(properties["performance"]) == 4
                    assert properties["performance"][0] >= 0
                    assert properties["status"] == "skip"
                    assert properties["retry"] == 4
                    assert properties["param"] is None
                    assert properties["class_param"] is None
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry3():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry3":
            for class_param, class_data in test.metrics.get_metrics().items():
                for test_param, properties in class_data.items():
                    if properties["param"] == 10 and properties["class_param"] == 1:
                        for i in properties["exceptions"]:
                            assert type(i) == Exception
                            assert str(i.with_traceback(None)) == "On purpose"
                        assert len(properties["performance"]) == 4
                        assert properties["performance"][0] >= 0
                        assert properties["status"] == "error"
                        assert properties["retry"] == 4
                        assert properties["param"] is not None
                        assert properties["class_param"] is not None
                    else:
                        assert properties["exceptions"] == [None]
                        assert len(properties["performance"]) == 1
                        assert properties["performance"][0] >= 0
                        assert properties["status"] == "success"
                        assert properties["retry"] == 1
                        assert properties["param"] is not None
                        assert properties["class_param"] is not None
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry4():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry4":
            for class_param, class_data in test.metrics.get_metrics().items():
                for test_param, properties in class_data.items():
                    if properties["param"] == 10:
                        for i in properties["exceptions"]:
                            assert type(i) == Exception
                            assert str(i.with_traceback(None)) == "On purpose"
                        assert len(properties["performance"]) == 4
                        assert properties["performance"][0] >= 0
                        assert properties["status"] == "error"
                        assert properties["retry"] == 4
                        assert properties["param"] is not None
                        assert properties["class_param"] is not None
                    else:
                        assert properties["exceptions"] == [None]
                        assert len(properties["performance"]) == 1
                        assert properties["performance"][0] >= 0
                        assert properties["status"] == "success"
                        assert properties["retry"] == 1
                        assert properties["param"] is not None
                        assert properties["class_param"] is not None
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry5():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry5":
            for class_param, class_data in test.metrics.get_metrics().items():
                for test_param, properties in class_data.items():
                    if properties["class_param"] == 1:
                        for i in properties["exceptions"]:
                            assert type(i) == Exception
                            assert str(i.with_traceback(None)) == "On purpose"
                        assert len(properties["performance"]) == 4
                        assert properties["performance"][0] >= 0
                        assert properties["status"] == "error"
                        assert properties["retry"] == 4
                        assert properties["param"] is not None
                        assert properties["class_param"] is not None
                    else:
                        assert properties["exceptions"] == [None]
                        assert len(properties["performance"]) == 1
                        assert properties["performance"][0] >= 0
                        assert properties["status"] == "success"
                        assert properties["retry"] == 1
                        assert properties["param"] is not None
                        assert properties["class_param"] is not None
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_skip():

    tested = False
    for test in tests:
        if test.get_function_name() == "skip":
            for class_param, class_data in test.metrics.get_metrics().items():
                for test_param, properties in class_data.items():
                    assert properties["exceptions"] == [None, None, None, None]
                    assert len(properties["performance"]) == 4
                    assert properties["performance"][0] >= 0
                    assert properties["status"] == "skip"
                    assert properties["retry"] == 4
                    assert properties["param"] is None
                    assert properties["class_param"] is None
                    tested = True
    if not tested:
        raise Exception("Test did not run")
