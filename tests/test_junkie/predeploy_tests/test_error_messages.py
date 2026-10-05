from test_junkie.decorators import Suite, test
from test_junkie.errors import BadParameters, TestJunkieExecutionError
from test_junkie.objects import _FuncEval
from test_junkie.runner import Runner
from test_junkie.settings import Settings

from tests.junkie_suites.error_messages.ErrorMessageSuites import BadSuitePrSuite, BadTestPrSuite


class _SkipObj:
    def __init__(self, skip_val, module="test_module", name="test_func"):
        self._skip = skip_val
        self._module = module
        self._name = name

    def get_skip(self): return self._skip
    def get_meta(self): return {}
    def get_function_module(self): return self._module
    def get_function_name(self): return self._name


def _raises_exception():
    raise RuntimeError("db connection refused")


def _returns_int():
    return 42


class _MethodHolder:
    def crashing(self):
        raise ValueError("method blew up")


def _bad_params_fn():
    raise ConnectionError("cannot reach database")


@Suite()
class ErrorMessageTestSuite:

    @test()
    def xml_report_extension_says_xml(self):
        raised = False
        try:
            Settings(runner_kwargs={}, run_kwargs={"xml_report": "/reports/out.txt"})
        except BadParameters as e:
            raised = True
            msg = str(e)
            assert ".xml" in msg
            assert ".html" not in msg
        assert raised

    @test()
    def eval_skip_crashing_function_names_function_and_error(self):
        obj = _SkipObj(_raises_exception, name="test_login")
        raised = False
        try:
            _FuncEval.eval_skip(obj)
        except TestJunkieExecutionError as e:
            raised = True
            msg = str(e)
            assert "_raises_exception" in msg
            assert "db connection refused" in msg
        assert raised

    @test()
    def eval_skip_wrong_return_type_names_test_and_type(self):
        obj = _SkipObj(_returns_int, module="tests.suite", name="test_checkout")
        raised = False
        try:
            _FuncEval.eval_skip(obj)
        except TestJunkieExecutionError as e:
            raised = True
            msg = str(e)
            assert "test_checkout" in msg
            assert "int" in msg
            assert "bool" in msg
        assert raised

    @test()
    def eval_skip_crashing_method_names_method_and_error(self):
        holder = _MethodHolder()
        obj = _SkipObj(holder.crashing, name="test_profile")
        raised = False
        try:
            _FuncEval.eval_skip(obj)
        except TestJunkieExecutionError as e:
            raised = True
            msg = str(e)
            assert "crashing" in msg
            assert "method blew up" in msg
        assert raised

    @test()
    def eval_params_crashing_function_names_function_and_error(self):
        raised = False
        try:
            _FuncEval.eval_params(_bad_params_fn)
        except TestJunkieExecutionError as e:
            raised = True
            msg = str(e)
            assert "_bad_params_fn" in msg
            assert "cannot reach database" in msg
        assert raised

    @test()
    def unregistered_suite_mentions_decorator_and_class(self):
        class _NotDecorated:
            pass
        raised = False
        try:
            Runner([_NotDecorated])
        except BadParameters as e:
            raised = True
            msg = str(e)
            assert "@Suite()" in msg
        assert raised

    @test()
    def suite_single_type_mismatch_message_is_clean(self):
        from test_junkie.builder import Builder
        from test_junkie.decorators import Suite as TjSuite, test as tj_test
        raised = False
        try:
            @TjSuite(priority="not_an_int")
            class _Bad:
                @tj_test()
                def test_x(self): pass
        except BadParameters as e:
            raised = True
            msg = str(e)
            assert "priority" in msg
            assert "int" in msg
            assert "[<class" not in msg
            assert "either type" not in msg
        finally:
            Builder._Builder__set_current_suite_object_defaults()
        assert raised

    @test()
    def suite_multi_type_mismatch_says_one_of(self):
        from test_junkie.builder import Builder
        from test_junkie.decorators import Suite as TjSuite, test as tj_test
        raised = False
        try:
            @TjSuite(skip=42)
            class _Bad:
                @tj_test()
                def test_x(self): pass
        except BadParameters as e:
            raised = True
            msg = str(e)
            assert "skip" in msg
            assert "one of" in msg
            assert "either type" not in msg
            assert "[<class" not in msg
        finally:
            Builder._Builder__set_current_suite_object_defaults()
        assert raised

    @test()
    def test_type_mismatch_message_is_clean(self):
        from test_junkie.builder import Builder
        from test_junkie.decorators import Suite as TjSuite, test as tj_test
        raised = False
        try:
            @TjSuite()
            class _Outer:
                @tj_test(retry="three")
                def test_x(self): pass
        except BadParameters as e:
            raised = True
            msg = str(e)
            assert "retry" in msg
            assert "int" in msg
            assert "[<class" not in msg
        finally:
            Builder._Builder__set_current_suite_object_defaults()
        assert raised

    @test()
    def bad_test_pr_type_raises_bad_parameters(self):
        raised = False
        try:
            Runner([BadTestPrSuite]).run()
        except BadParameters as e:
            raised = True
            msg = str(e)
            assert "test_a" in msg
        except Exception:
            raise AssertionError("should raise BadParameters, not a bare Exception")
        assert raised

    @test()
    def bad_suite_pr_type_raises_bad_parameters(self):
        raised = False
        try:
            Runner([BadSuitePrSuite], suite_multithreading_limit=2).run()
        except BadParameters as e:
            raised = True
            msg = str(e)
            assert "BadSuitePrSuite" in msg
        except Exception:
            raise AssertionError("should raise BadParameters, not a bare Exception")
        assert raised
