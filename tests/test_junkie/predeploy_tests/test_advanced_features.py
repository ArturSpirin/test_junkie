from test_junkie.decorators import Suite, test, beforeClass
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.AdvancedSuite import AdvancedSuite


@Suite()
class AdvancedFeaturesSuite:

    _results = None
    _tests = None

    @beforeClass()
    def setup(self):
        runner = Runner([AdvancedSuite])
        runner.run(suite_multithreading=True, suite_multithreading_limit=5,
                   test_multithreading=True, test_multithreading_limit=5,
                   tag_config={"run_on_match_all": ["critical", "v2"],
                               "run_on_match_any": ["critical2"],
                               "skip_on_match_all": ["skip", "v2"],
                               "skip_on_match_any": ["trivial"]})
        AdvancedFeaturesSuite._results = runner.get_executed_suites()
        AdvancedFeaturesSuite._tests = AdvancedFeaturesSuite._results[0].get_test_objects()

    @test()
    def class_stats(self):
        metrics = AdvancedFeaturesSuite._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_status="fail",
                                           expected_retry_count=2,
                                           expected_beforeclass_exception_count=4,
                                           expected_beforeclass_exception_object=None,
                                           expected_beforeclass_performance_count=4,
                                           expected_afterclass_exception_count=4,
                                           expected_afterclass_exception_object=None,
                                           expected_afterclass_performance_count=4,
                                           expected_beforetest_exception_count=29,
                                           expected_beforetest_exception_object=None,
                                           expected_beforetest_performance_count=29,
                                           expected_aftertest_exception_count=29,
                                           expected_aftertest_exception_object=None,
                                           expected_aftertest_performance_count=29)

    @test()
    def no_retry(self):
        found = next((t for t in AdvancedFeaturesSuite._tests
                      if t.get_function_name() == "no_retry"), None)
        assert found is not None, "test 'no_retry' not found"
        for class_param, class_data in found.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics, expected_status="success",
                                                  expected_param=param,
                                                  expected_class_param=metrics["class_param"])

    @test()
    def no_retry2(self):
        found = next((t for t in AdvancedFeaturesSuite._tests
                      if t.get_function_name() == "no_retry2"), None)
        assert found is not None, "test 'no_retry2' not found"
        for class_param, class_data in found.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics, expected_status="success",
                                                  expected_param=param,
                                                  expected_class_param=metrics["class_param"])

    @test()
    def no_retry3(self):
        found = next((t for t in AdvancedFeaturesSuite._tests
                      if t.get_function_name() == "no_retry3"), None)
        assert found is not None, "test 'no_retry3' not found"
        for class_param, class_data in found.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics, expected_status="success",
                                                  expected_param=param,
                                                  expected_class_param=metrics["class_param"])

    @test()
    def retry(self):
        found = next((t for t in AdvancedFeaturesSuite._tests
                      if t.get_function_name() == "retry"), None)
        assert found is not None, "test 'retry' not found"
        for class_param, class_data in found.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics, expected_status="fail",
                                                  expected_exception=AssertionError,
                                                  expected_retry_count=4,
                                                  expected_exception_count=4,
                                                  expected_performance_count=4,
                                                  expected_class_param=metrics["class_param"])
                for exc in metrics["exceptions"]:
                    assert str(exc.with_traceback(None)) == "Expected Assertion Error"

    @test()
    def retry2(self):
        found = next((t for t in AdvancedFeaturesSuite._tests
                      if t.get_function_name() == "retry2"), None)
        assert found is not None, "test 'retry2' not found"
        for class_param, class_data in found.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics, expected_status="skip",
                                                  expected_retry_count=2,
                                                  expected_exception_count=2,
                                                  expected_performance_count=2)

    @test()
    def retry3(self):
        found = next((t for t in AdvancedFeaturesSuite._tests
                      if t.get_function_name() == "retry3"), None)
        assert found is not None, "test 'retry3' not found"
        for class_param, class_data in found.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                if metrics["param"] == 10 and metrics["class_param"] == 1:
                    QualityManager.check_test_metrics(metrics, expected_status="error",
                                                      expected_exception=Exception,
                                                      expected_retry_count=4,
                                                      expected_exception_count=4,
                                                      expected_performance_count=4,
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])
                    for exc in metrics["exceptions"]:
                        assert str(exc.with_traceback(None)) == "On purpose"
                else:
                    QualityManager.check_test_metrics(metrics, expected_status="success",
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])

    @test()
    def retry4(self):
        found = next((t for t in AdvancedFeaturesSuite._tests
                      if t.get_function_name() == "retry4"), None)
        assert found is not None, "test 'retry4' not found"
        for class_param, class_data in found.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                if metrics["param"] == 10:
                    QualityManager.check_test_metrics(metrics, expected_status="error",
                                                      expected_exception=Exception,
                                                      expected_retry_count=4,
                                                      expected_exception_count=4,
                                                      expected_performance_count=4,
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])
                    for exc in metrics["exceptions"]:
                        assert str(exc.with_traceback(None)) == "On purpose"
                else:
                    QualityManager.check_test_metrics(metrics, expected_status="success",
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])

    @test()
    def retry5(self):
        found = next((t for t in AdvancedFeaturesSuite._tests
                      if t.get_function_name() == "retry5"), None)
        assert found is not None, "test 'retry5' not found"
        for class_param, class_data in found.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                if metrics["class_param"] == 1:
                    QualityManager.check_test_metrics(metrics, expected_status="error",
                                                      expected_exception=Exception,
                                                      expected_retry_count=4,
                                                      expected_exception_count=4,
                                                      expected_performance_count=4,
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])
                    for exc in metrics["exceptions"]:
                        assert str(exc.with_traceback(None)) == "On purpose"
                else:
                    QualityManager.check_test_metrics(metrics, expected_status="success",
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])

    @test()
    def skip(self):
        found = next((t for t in AdvancedFeaturesSuite._tests
                      if t.get_function_name() == "skip"), None)
        assert found is not None, "test 'skip' not found"
        for class_param, class_data in found.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics, expected_status="skip",
                                                  expected_retry_count=2,
                                                  expected_exception_count=2,
                                                  expected_performance_count=2)
