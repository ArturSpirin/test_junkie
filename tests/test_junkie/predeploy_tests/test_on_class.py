import threading

from test_junkie.decorators import Suite, test, beforeClass
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.CancelSuite import CancelSuite
from tests.junkie_suites.IgnoreSuite import (IgnoreSuiteBoundMethod, IgnoreSuiteFunction, IgnoreSuiteClassic,
                                              IgnoreSuiteClassic2, IgnoreSuiteClassic3)
from tests.junkie_suites.SkipSuite import SkipSuite
from tests.junkie_suites.error_handling.ErrorSuite4 import ErrorSuite4
from tests.junkie_suites.error_handling.ErrorSuite5 import ErrorSuite5
from tests.junkie_suites.error_handling.ErrorSuite6 import ErrorSuite6


@Suite()
class CancelSuiteTests:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([CancelSuite])
        thread = threading.Thread(target=runner.run)
        runner.cancel()
        thread.start()
        thread.join()
        CancelSuiteTests._results = runner.get_executed_suites()

    @test()
    def cancel_class_metrics(self):
        metrics = CancelSuiteTests._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics, expected_retry_count=0, expected_status="cancel")

    @test()
    def cancel_tests_have_no_metrics(self):
        assert CancelSuiteTests._results[0].get_test_objects()
        for t in CancelSuiteTests._results[0].get_test_objects():
            assert len(t.metrics.get_metrics()) == 0


@Suite()
class IgnoreSuiteTests:

    @test()
    def ignore_bound_method(self):
        r = Runner([IgnoreSuiteBoundMethod])
        r.run()
        s = r.get_executed_suites()
        QualityManager.check_class_metrics(s[0].metrics.get_metrics(),
                                           expected_status="ignore", expected_retry_count=0)

    @test()
    def ignore_bound_method_test_metrics(self):
        r = Runner([IgnoreSuiteBoundMethod])
        r.run()
        s = r.get_executed_suites()
        assert s[0].get_test_objects()
        for t in s[0].get_test_objects():
            assert len(t.metrics.get_metrics()) == 0

    @test()
    def ignore_function(self):
        r = Runner([IgnoreSuiteFunction])
        r.run()
        s = r.get_executed_suites()
        QualityManager.check_class_metrics(s[0].metrics.get_metrics(),
                                           expected_status="ignore", expected_retry_count=0)

    @test()
    def ignore_function_test_metrics(self):
        r = Runner([IgnoreSuiteFunction])
        r.run()
        s = r.get_executed_suites()
        assert s[0].get_test_objects()
        for t in s[0].get_test_objects():
            assert len(t.metrics.get_metrics()) == 0

    @test()
    def ignore_classic(self):
        r = Runner([IgnoreSuiteClassic])
        r.run()
        s = r.get_executed_suites()
        QualityManager.check_class_metrics(s[0].metrics.get_metrics(),
                                           expected_status="ignore", expected_retry_count=0)

    @test()
    def ignore_classic_test_metrics(self):
        r = Runner([IgnoreSuiteClassic])
        r.run()
        s = r.get_executed_suites()
        assert s[0].get_test_objects()
        for t in s[0].get_test_objects():
            assert len(t.metrics.get_metrics()) == 0

    @test()
    def ignore_classic2(self):
        r = Runner([IgnoreSuiteClassic2])
        r.run()
        s = r.get_executed_suites()
        QualityManager.check_class_metrics(s[0].metrics.get_metrics(),
                                           expected_status="ignore", expected_retry_count=0)

    @test()
    def ignore_classic2_test_metrics(self):
        r = Runner([IgnoreSuiteClassic2])
        r.run()
        s = r.get_executed_suites()
        assert s[0].get_test_objects()
        for t in s[0].get_test_objects():
            assert len(t.metrics.get_metrics()) == 0

    @test()
    def ignore_classic3(self):
        r = Runner([IgnoreSuiteClassic3])
        r.run()
        s = r.get_executed_suites()
        QualityManager.check_class_metrics(s[0].metrics.get_metrics(),
                                           expected_status="ignore", expected_retry_count=0)

    @test()
    def ignore_classic3_test_metrics(self):
        r = Runner([IgnoreSuiteClassic3])
        r.run()
        s = r.get_executed_suites()
        assert s[0].get_test_objects()
        for t in s[0].get_test_objects():
            assert len(t.metrics.get_metrics()) == 0


@Suite()
class SkipSuiteTests:

    @test()
    def skip_class_metrics(self):
        r = Runner([SkipSuite])
        r.run()
        s = r.get_executed_suites()
        metrics = s[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics, expected_status="skip", expected_retry_count=0)

    @test()
    def skip_tests_have_no_metrics(self):
        r = Runner([SkipSuite])
        r.run()
        s = r.get_executed_suites()
        assert s[0].get_test_objects()
        for t in s[0].get_test_objects():
            assert len(t.metrics.get_metrics()) == 0


@Suite()
class ErrorSuiteTests:

    @test()
    def wrong_params_raises_bad_parameters(self):
        from test_junkie.errors import BadParameters
        raised = False
        try:
            from tests.junkie_suites.error_handling import ErrorSuite1
        except BadParameters:
            raised = True
        except Exception:
            pass
        assert raised

    @test()
    def wrong_params2_raises_bad_signature(self):
        from test_junkie.errors import BadSignature
        raised = False
        try:
            from tests.junkie_suites.error_handling import ErrorSuite2
        except BadSignature:
            raised = True
        except Exception:
            pass
        assert raised

    @test()
    def wrong_params3_raises_bad_parameters(self):
        from test_junkie.errors import BadParameters
        raised = False
        try:
            from tests.junkie_suites.error_handling.ErrorSuite3 import ErrorSuite3
        except BadParameters:
            raised = True
        except Exception:
            pass
        assert raised

    @test()
    def beforeTest_error_class_metrics(self):
        r = Runner([ErrorSuite4])
        r.run()
        s = r.get_executed_suites()
        QualityManager.check_class_metrics(s[0].metrics.get_metrics(),
                                           expected_status="fail", expected_retry_count=1,
                                           expected_beforetest_performance_count=1,
                                           expected_beforetest_exception_object=Exception,
                                           expected_beforetest_exception_count=1)

    @test()
    def beforeTest_error_test_metrics(self):
        r = Runner([ErrorSuite4])
        r.run()
        s = r.get_executed_suites()
        for t in s[0].get_test_objects():
            if t.get_function_name() == "failure":
                metrics = t.metrics.get_metrics()["None"]["None"]
                QualityManager.check_test_metrics(metrics, expected_status="error", expected_exception=Exception)

    @test()
    def afterTest_error_class_metrics(self):
        r = Runner([ErrorSuite5])
        r.run()
        s = r.get_executed_suites()
        QualityManager.check_class_metrics(s[0].metrics.get_metrics(),
                                           expected_status="fail", expected_retry_count=1,
                                           expected_aftertest_performance_count=1,
                                           expected_aftertest_exception_object=Exception,
                                           expected_aftertest_exception_count=1)

    @test()
    def afterTest_error_test_metrics(self):
        r = Runner([ErrorSuite5])
        r.run()
        s = r.get_executed_suites()
        for t in s[0].get_test_objects():
            if t.get_function_name() == "failure":
                metrics = t.metrics.get_metrics()["None"]["None"]
                QualityManager.check_test_metrics(metrics, expected_status="error", expected_exception=Exception)

    @test()
    def bad_suite_inputs_raise_bad_parameters(self):
        from test_junkie.errors import BadParameters
        raised = False
        try:
            Runner([ErrorSuite6]).run()
        except BadParameters:
            raised = True
        assert raised

