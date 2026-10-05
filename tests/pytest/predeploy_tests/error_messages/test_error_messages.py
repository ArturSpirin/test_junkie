"""
Negative-path tests for all 7 improved error messages.

1  settings.xml_report      wrong extension message says ".xml" not ".html"
2  eval_skip / function raises        message names the function and the original error
3  eval_skip / wrong return type      message names the test and the returned type
4  eval_skip / bound method raises    message names the method and the original error
5  eval_params / function raises      message names the function and the original error
6  runner.__prioritize / unregistered suite   names the class, mentions @Suite()
7  builder @Suite() single-type mismatch      plain type name, no "[<class>]" brackets
8  builder @Suite() multi-type mismatch       "one of: ..." wording, not "either type"
9  builder @test() type mismatch              names arg, plain type name
10 parallels bad test pr= type               BadParameters (not Exception), names test
11 parallels bad suite pr= type              BadParameters (not Exception), names suite
"""
from test_junkie.errors import BadParameters, TestJunkieExecutionError
from test_junkie.objects import _FuncEval
from test_junkie.runner import Runner
from test_junkie.settings import Settings

from tests.junkie_suites.error_messages.ErrorMessageSuites import BadSuitePrSuite, BadTestPrSuite


# ── helpers ───────────────────────────────────────────────────────────────────

class _SkipObj:
    """Minimal duck-typed stand-in for SuiteObject/TestObject used by _FuncEval."""
    def __init__(self, skip_val, module="test_module", name="test_func"):
        self._skip = skip_val
        self._module = module
        self._name = name
    def get_skip(self):        return self._skip
    def get_meta(self):        return {}
    def get_function_module(self): return self._module
    def get_function_name(self):   return self._name


def _raises_exception():
    raise RuntimeError("db connection refused")


def _returns_int():
    return 42


class _MethodHolder:
    def crashing(self):
        raise ValueError("method blew up")


# ── 1. settings.xml_report extension ─────────────────────────────────────────

def test_xml_report_wrong_extension_message_says_xml_not_html():
    # Settings.__init__ calls __print_settings() which accesses xml_report, so the
    # exception fires during construction.
    raised = False
    try:
        Settings(runner_kwargs={}, run_kwargs={"xml_report": "/reports/out.txt"})
    except BadParameters as e:
        raised = True
        msg = str(e)
        assert ".xml" in msg, "message should mention .xml extension"
        assert ".html" not in msg, "message must not say .html (regression: copy-paste bug)"
    assert raised


# ── 2. eval_skip: skip function raises an exception ───────────────────────────

def test_eval_skip_crashing_function_names_function_and_error():
    obj = _SkipObj(_raises_exception, name="test_login")
    raised = False
    try:
        _FuncEval.eval_skip(obj)
    except TestJunkieExecutionError as e:
        raised = True
        msg = str(e)
        assert "_raises_exception" in msg, "message should include the function name"
        assert "db connection refused" in msg, "message should include the original error"
    assert raised


# ── 3. eval_skip: skip function returns wrong type ────────────────────────────

def test_eval_skip_wrong_return_type_names_test_and_type():
    obj = _SkipObj(_returns_int, module="tests.suite", name="test_checkout")
    raised = False
    try:
        _FuncEval.eval_skip(obj)
    except TestJunkieExecutionError as e:
        raised = True
        msg = str(e)
        assert "test_checkout" in msg, "message should include the test name"
        assert "int" in msg, "message should include the returned type"
        assert "bool" in msg, "message should say bool was expected"
    assert raised


# ── 4. eval_skip: bound method raises an exception ───────────────────────────

def test_eval_skip_crashing_method_names_method_and_error():
    holder = _MethodHolder()
    obj = _SkipObj(holder.crashing, name="test_profile")
    raised = False
    try:
        _FuncEval.eval_skip(obj)
    except TestJunkieExecutionError as e:
        raised = True
        msg = str(e)
        assert "crashing" in msg, "message should include the method name"
        assert "method blew up" in msg, "message should include the original error"
    assert raised


# ── 5. eval_params: parameters function raises an exception ──────────────────

def _bad_params_fn():
    raise ConnectionError("cannot reach database")


def test_eval_params_crashing_function_names_function_and_error():
    raised = False
    try:
        _FuncEval.eval_params(_bad_params_fn)
    except TestJunkieExecutionError as e:
        raised = True
        msg = str(e)
        assert "_bad_params_fn" in msg, "message should include the function name"
        assert "cannot reach database" in msg, "message should include the original error"
    assert raised


# ── 6. runner.__prioritize: unregistered suite ───────────────────────────────

def test_unregistered_suite_mentions_decorator_and_class():
    class _NotDecorated:
        pass

    raised = False
    try:
        Runner([_NotDecorated])
    except BadParameters as e:
        raised = True
        msg = str(e)
        assert "@Suite()" in msg, "message should tell the user to add @Suite()"
        assert "registered" in msg or "not found" in msg.lower() or "_NotDecorated" in msg
    assert raised


# ── 7. builder @Suite(): single-type mismatch — no raw list brackets ─────────

def test_suite_single_type_mismatch_message_is_clean():
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
        assert "priority" in msg, "message should name the bad argument"
        assert "int" in msg, "message should name the expected type"
        assert "[<class" not in msg, "no raw list/class repr in message"
        assert "either type" not in msg, "old wording must be gone"
    finally:
        Builder._Builder__set_current_suite_object_defaults()
    assert raised


# ── 8. builder @Suite(): multi-type — "one of: ..." not "either type" ────────

def test_suite_multi_type_mismatch_says_one_of():
    from test_junkie.builder import Builder
    from test_junkie.decorators import Suite as TjSuite, test as tj_test

    raised = False
    try:
        @TjSuite(skip=42)   # skip accepts bool or function — two valid types
        class _Bad:
            @tj_test()
            def test_x(self): pass
    except BadParameters as e:
        raised = True
        msg = str(e)
        assert "skip" in msg, "message should name the bad argument"
        assert "one of" in msg, "message should use 'one of' for multiple valid types"
        assert "either type" not in msg, "old wording must be gone"
        assert "[<class" not in msg, "no raw list/class repr in message"
    finally:
        Builder._Builder__set_current_suite_object_defaults()
    assert raised


# ── 9. builder @test(): type mismatch — clean message ────────────────────────

def test_test_type_mismatch_message_is_clean():
    from test_junkie.builder import Builder
    from test_junkie.decorators import Suite as TjSuite, test as tj_test

    raised = False
    try:
        @TjSuite()
        class _Outer:
            @tj_test(retry="three")   # retry expects int
            def test_x(self): pass
    except BadParameters as e:
        raised = True
        msg = str(e)
        assert "retry" in msg, "message should name the bad argument"
        assert "int" in msg, "message should name the expected type"
        assert "[<class" not in msg, "no raw list/class repr in message"
        assert "either type" not in msg, "old wording must be gone"
    finally:
        Builder._Builder__set_current_suite_object_defaults()
    assert raised


# ── 10. parallels: bad test pr= type — BadParameters, not bare Exception ─────

def test_test_bad_pr_type_raises_bad_parameters_not_exception():
    raised = False
    try:
        Runner([BadTestPrSuite]).run()
    except BadParameters as e:
        raised = True
        msg = str(e)
        assert "test_a" in msg, "message should include the test name"
        assert "type" in msg.lower(), "message should mention the type"
    except Exception:
        assert False, "should raise BadParameters, not a bare Exception"
    assert raised


# ── 11. parallels: bad suite pr= type — BadParameters, not bare Exception ────

def test_suite_bad_pr_type_raises_bad_parameters_not_exception():
    raised = False
    try:
        Runner([BadSuitePrSuite], suite_multithreading_limit=2).run()
    except BadParameters as e:
        raised = True
        msg = str(e)
        assert "BadSuitePrSuite" in msg, "message should include the suite name"
        assert "type" in msg.lower(), "message should mention the type"
    except Exception:
        assert False, "should raise BadParameters, not a bare Exception"
    assert raised
