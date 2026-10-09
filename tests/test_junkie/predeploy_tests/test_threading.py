from test_junkie.decorators import Suite, test, beforeClass
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.ParallelSuiteA import ParallelSuiteA
from tests.junkie_suites.ParallelSuiteB import ParallelSuiteB
from tests.junkie_suites.ParallelSuiteC import ParallelSuiteC


@Suite()
class ThreadingTestSuite:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([ParallelSuiteA, ParallelSuiteB, ParallelSuiteC])
        runner.run(test_multithreading_limit=2, suite_multithreading_limit=2)
        ThreadingTestSuite._results = runner.get_executed_suites()

    @test()
    def class_metrics_suite_a(self):
        assert ThreadingTestSuite._results[0].get_class_name() == "ParallelSuiteA"
        metrics = ThreadingTestSuite._results[0].metrics.get_metrics()
        # ParallelSuiteA declares pr=[ParallelSuiteC]: the two never run at the same time. (This used to assert that A
        # finished faster than B and C, which only held while pr= let conflicting tests slip in between parameters.)
        other = ThreadingTestSuite._results[2].metrics.get_metrics()
        assert metrics["end"] <= other["start"] or other["end"] <= metrics["start"]
        QualityManager.check_class_metrics(metrics, expected_status="success", expected_retry_count=1)

    @test()
    def test_metrics_suite_a(self):
        assert ThreadingTestSuite._results[0].get_test_objects()
        for t in ThreadingTestSuite._results[0].get_test_objects():
            for class_param, class_data in t.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    QualityManager.check_test_metrics(metrics, expected_status="success",
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])

    @test()
    def class_metrics_suite_b(self):
        assert ThreadingTestSuite._results[1].get_class_name() == "ParallelSuiteB"
        metrics = ThreadingTestSuite._results[1].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics, expected_status="success", expected_retry_count=1)

    @test()
    def test_metrics_suite_b(self):
        assert ThreadingTestSuite._results[1].get_test_objects()
        for t in ThreadingTestSuite._results[1].get_test_objects():
            for class_param, class_data in t.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    QualityManager.check_test_metrics(metrics, expected_status="success",
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])

    @test()
    def class_metrics_suite_c(self):
        assert ThreadingTestSuite._results[2].get_class_name() == "ParallelSuiteC"
        metrics = ThreadingTestSuite._results[2].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics, expected_status="success", expected_retry_count=1)

    @test()
    def test_metrics_suite_c(self):
        assert ThreadingTestSuite._results[2].get_test_objects()
        for t in ThreadingTestSuite._results[2].get_test_objects():
            for class_param, class_data in t.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    QualityManager.check_test_metrics(metrics, expected_status="success",
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])
