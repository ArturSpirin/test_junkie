from test_junkie.decorators import test, beforeClass, Suite
from test_junkie.runner import Runner


@Suite(retry=2)
class IgnoreUseCases:

    @beforeClass()
    def before_class(self):
        raise Exception("Exception in before class")

    @test(retry=2)
    def ignore_1(self):
        pass

    @test(retry=2)
    def ignore_2(self):
        pass


runner = Runner(IgnoreUseCases)
runner.run()
results = runner.get_executed_suites()


def test_ignore_class_metrics():

    class_stats = results[0].metrics.get_metrics()
    assert class_stats["retry"] == 2
    assert class_stats["status"] == "fail"
    assert class_stats["runtime"] >= 0

    assert len(class_stats["afterClass"]["exceptions"]) == 0
    assert class_stats["afterClass"]["exceptions"] == []
    assert len(class_stats["afterClass"]["performance"]) == 0

    assert len(class_stats["beforeClass"]["exceptions"]) == 2
    for i in class_stats["beforeClass"]["exceptions"]:
        assert isinstance(i, Exception)
    assert len(class_stats["beforeClass"]["performance"]) == 2

    assert len(class_stats["beforeTest"]["exceptions"]) == 0
    assert len(class_stats["beforeTest"]["performance"]) == 0

    assert len(class_stats["afterTest"]["performance"]) == 0
    assert len(class_stats["afterTest"]["exceptions"]) == 0


def test_ignore_test_metrics():

    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()["None"]["None"]
        for i in properties["exceptions"]:
            assert isinstance(i, Exception)
        assert len(properties["exceptions"]) == 2
        assert len(properties["performance"]) == 2
        for i in properties["performance"]:
            assert i >= 0
        assert properties["status"] == "ignore"
        assert properties["retry"] == 2
        assert properties["param"] is None


@Suite(retry=2)
class IgnoreUseCases2:

    @beforeClass()
    def before_class(self):
        raise AssertionError("Assertion Error in before class")

    @test(retry=2)
    def ignore_1(self):
        pass

    @test(retry=2)
    def ignore_2(self):
        pass


runner = Runner(IgnoreUseCases2)
runner.run()
results = runner.get_executed_suites()

def test_ignore_class_metrics2():

    class_stats = results[0].metrics.get_metrics()
    assert class_stats["retry"] == 2
    assert class_stats["status"] == "fail"
    assert class_stats["runtime"] >= 0

    assert len(class_stats["afterClass"]["exceptions"]) == 0
    assert class_stats["afterClass"]["exceptions"] == []
    assert len(class_stats["afterClass"]["performance"]) == 0

    assert len(class_stats["beforeClass"]["exceptions"]) == 2
    for i in class_stats["beforeClass"]["exceptions"]:
        assert isinstance(i, Exception)
    assert len(class_stats["beforeClass"]["performance"]) == 2

    assert len(class_stats["beforeTest"]["exceptions"]) == 0
    assert len(class_stats["beforeTest"]["performance"]) == 0

    assert len(class_stats["afterTest"]["performance"]) == 0
    assert len(class_stats["afterTest"]["exceptions"]) == 0


def test_ignore_test_metrics2():

    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()["None"]["None"]
        for i in properties["exceptions"]:
            assert isinstance(i, Exception)
        assert len(properties["exceptions"]) == 2
        assert len(properties["performance"]) == 2
        for i in properties["performance"]:
            assert i >= 0
        assert properties["status"] == "ignore"
        assert properties["retry"] == 2
        assert properties["param"] is None
