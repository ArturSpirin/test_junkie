from test_junkie.constants import TestCategory, DecoratorType
from test_junkie.decorators import Suite, test, beforeClass
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.BasicSuite import BasicSuite
from tests.junkie_suites.ExecutionSquence import ExecutionSequence1, ExecutionSequence2, ExecutionSequence3, \
    ExecutionSequence4
from tests.junkie_suites.ParametersSuite import ParametersSuite


@Suite()
class BasicFeaturesSuite:

    _results = None
    _tests = None

    @beforeClass()
    def setup(self):
        runner = Runner([BasicSuite])
        runner.run()
        BasicFeaturesSuite._results = runner.get_executed_suites()
        BasicFeaturesSuite._tests = BasicFeaturesSuite._results[0].get_test_objects()

    @test()
    def class_metrics(self):
        metrics = BasicFeaturesSuite._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_status="fail",
                                           expected_beforeclass_exception_count=1,
                                           expected_beforeclass_exception_object=None,
                                           expected_beforeclass_performance_count=1,
                                           expected_afterclass_exception_count=1,
                                           expected_afterclass_exception_object=None,
                                           expected_afterclass_performance_count=1,
                                           expected_beforetest_exception_count=8,
                                           expected_beforetest_exception_object=None,
                                           expected_beforetest_performance_count=8,
                                           expected_aftertest_exception_count=8,
                                           expected_aftertest_exception_object=None,
                                           expected_aftertest_performance_count=8)

    @test()
    def failure_test(self):
        found = next((t for t in BasicFeaturesSuite._tests
                      if t.get_function_name() == "failure"), None)
        assert found is not None, "test 'failure' not found"
        metrics = found.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics, expected_status="fail", expected_exception=AssertionError)

    @test()
    def error_test(self):
        found = next((t for t in BasicFeaturesSuite._tests
                      if t.get_function_name() == "error"), None)
        assert found is not None, "test 'error' not found"
        metrics = found.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics, expected_status="error", expected_exception=Exception)

    @test()
    def skip_test(self):
        found = next((t for t in BasicFeaturesSuite._tests
                      if t.get_function_name() == "skip"), None)
        assert found is not None, "test 'skip' not found"
        metrics = found.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics, expected_status="skip")

    @test()
    def skip_function_test(self):
        found = next((t for t in BasicFeaturesSuite._tests
                      if t.get_function_name() == "skip_function"), None)
        assert found is not None, "test 'skip_function' not found"
        metrics = found.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics, expected_status="skip")

    @test()
    def retry_test(self):
        found = next((t for t in BasicFeaturesSuite._tests
                      if t.get_function_name() == "retry"), None)
        assert found is not None, "test 'retry' not found"
        metrics = found.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics, expected_status="fail", expected_exception=AssertionError,
                                          expected_retry_count=2, expected_performance_count=2,
                                          expected_exception_count=2)

    @test()
    def parameters_test(self):
        found = next((t for t in BasicFeaturesSuite._tests
                      if t.get_function_name() == "parameters"), None)
        assert found is not None, "test 'parameters' not found"
        for param, metrics in found.metrics.get_metrics()["None"].items():
            QualityManager.check_test_metrics(metrics, expected_status="success", expected_param=param)

    @test()
    def parameters_plus_plus(self):
        runner = Runner([ParametersSuite])
        aggregator = runner.run()
        metrics = aggregator.get_basic_report()["tests"]
        assert metrics[TestCategory.SUCCESS] == 36
        assert metrics[TestCategory.IGNORE] == 4
        suites = runner.get_executed_suites()
        QualityManager.check_class_metrics(suites[0].metrics.get_metrics(), expected_status="fail")

    @test()
    def execution_sequence1(self):
        runner = Runner([ExecutionSequence1])
        aggregator = runner.run()
        metrics = aggregator.get_basic_report()["tests"]
        assert metrics[TestCategory.SUCCESS] == 0
        assert metrics[TestCategory.FAIL] == 6
        suites = runner.get_executed_suites()
        QualityManager.check_class_metrics(suites[0].metrics.get_metrics(),
                                           expected_status="fail", expected_retry_count=2,
                                           expected_beforetest_exception_count=20,
                                           expected_beforetest_performance_count=20,
                                           expected_beforetest_exception_object=AssertionError,
                                           expected_aftertest_exception_count=20,
                                           expected_aftertest_performance_count=20,
                                           expected_aftertest_exception_object=None)
        for t in suites[0].get_test_objects():
            for _, class_param_data in t.metrics.get_metrics().items():
                for _, param_data in class_param_data.items():
                    expected = 4 if param_data["param"] is not None else 2
                    assert len(param_data[DecoratorType.BEFORE_TEST]["exceptions"]) == expected
                    assert len(param_data[DecoratorType.BEFORE_TEST]["tracebacks"]) == expected
                    assert len(param_data[DecoratorType.BEFORE_TEST]["performance"]) == expected

    @test()
    def execution_sequence2(self):
        runner = Runner([ExecutionSequence2])
        aggregator = runner.run()
        metrics = aggregator.get_basic_report()["tests"]
        assert metrics[TestCategory.SUCCESS] == 0
        assert metrics[TestCategory.FAIL] == 6
        suites = runner.get_executed_suites()
        QualityManager.check_class_metrics(suites[0].metrics.get_metrics(),
                                           expected_status="fail", expected_retry_count=2,
                                           expected_beforetest_exception_count=20,
                                           expected_beforetest_performance_count=20,
                                           expected_beforetest_exception_object=None,
                                           expected_aftertest_exception_count=20,
                                           expected_aftertest_performance_count=20,
                                           expected_aftertest_exception_object=AssertionError)

    @test()
    def execution_sequence3(self):
        runner = Runner([ExecutionSequence3])
        aggregator = runner.run()
        metrics = aggregator.get_basic_report()["tests"]
        assert metrics[TestCategory.SUCCESS] == 5
        assert metrics[TestCategory.FAIL] == 1
        suites = runner.get_executed_suites()
        QualityManager.check_class_metrics(suites[0].metrics.get_metrics(),
                                           expected_status="fail", expected_retry_count=2,
                                           expected_beforetest_exception_count=7,
                                           expected_beforetest_performance_count=7,
                                           expected_beforetest_exception_object=None,
                                           expected_aftertest_exception_count=7,
                                           expected_aftertest_performance_count=7,
                                           expected_aftertest_exception_object=None)

    @test()
    def execution_sequence4(self):
        runner = Runner([ExecutionSequence4])
        aggregator = runner.run()
        metrics = aggregator.get_basic_report()["tests"]
        assert metrics[TestCategory.SUCCESS] == 6
        assert metrics[TestCategory.FAIL] == 0
        suites = runner.get_executed_suites()
        QualityManager.check_class_metrics(suites[0].metrics.get_metrics(), expected_status="success")

