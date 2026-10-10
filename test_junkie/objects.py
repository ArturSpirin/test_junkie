import copy
import functools
import fnmatch
import inspect
import threading
import time
import traceback
from test_junkie.decorators import DecoratorType
from test_junkie.constants import DocumentationLinks, TestCategory
from test_junkie.errors import TestJunkieExecutionError, BadParameters
from test_junkie.metrics import ClassMetrics, TestMetrics, Aggregator
from test_junkie.params import param_key, register as register_ids

_DECLARED = object()  # SuiteObject.get_meta(): no suite parameter given, the declared meta only


@functools.lru_cache(maxsize=None)
def _cached_arg_names(func):
    return inspect.getfullargspec(func).args


def arg_names(func):
    """
    :return: LIST of the function's argument names. Cached - inspect.getfullargspec() was called ~6 times per test
    """
    try:
        return _cached_arg_names(func)
    except TypeError:  # unhashable callable
        return inspect.getfullargspec(func).args

class _FuncEval:

    @staticmethod
    def eval_skip(obj):

        val = obj.get_skip()
        if not isinstance(val, bool):
            if inspect.isfunction(val):
                try:
                    val = val(meta=obj.get_meta()) if "meta" in arg_names(val) else val()
                except Exception as e:
                    raise TestJunkieExecutionError(
                        "skip function '{name}' in {mod}.{test} raised an unexpected error: {err}. "
                        "See documentation: {link}".format(
                            name=val.__name__, mod=obj.get_function_module(),
                            test=obj.get_function_name(), err=e, link=DocumentationLinks.SKIP)) from e
            elif inspect.ismethod(val):
                try:
                    val = getattr(val.__self__, val.__name__)(meta=obj.get_meta()) \
                        if "meta" in arg_names(val) \
                        else getattr(val.__self__, val.__name__)()
                except Exception as e:
                    raise TestJunkieExecutionError(
                        "skip method '{name}' in {mod}.{test} raised an unexpected error: {err}. "
                        "See documentation: {link}".format(
                            name=val.__name__, mod=obj.get_function_module(),
                            test=obj.get_function_name(), err=e, link=DocumentationLinks.SKIP)) from e
            else:
                raise BadParameters(
                    "skip= in {mod}.{test} received {got}, which is not a supported type. "
                    "Expected: bool, a function, or a bound method. See documentation: {link}".format(
                        mod=obj.get_function_module(), test=obj.get_function_name(),
                        got=type(val).__name__, link=DocumentationLinks.SKIP))
            if not isinstance(val, bool):
                raise TestJunkieExecutionError(
                    "skip function for {mod}.{test} must return bool but returned {got}. "
                    "See documentation: {link}".format(
                        mod=obj.get_function_module(), test=obj.get_function_name(),
                        got=type(val).__name__, link=DocumentationLinks.SKIP))
        return val

    # parameter functions that raised during this run -> the error to raise again: a provider that timed out isn't
    # called again for every suite or test sharing it. Cleared by Runner.run() at the start of each run
    provider_failures = {}
    _provider_lock = threading.Lock()

    @staticmethod
    def eval_params(params):

        if not (inspect.isfunction(params) or inspect.ismethod(params)):
            return params
        key = (getattr(params, "__self__", None) is not None and id(params.__self__), params.__qualname__,
               getattr(params, "__func__", params))
        with _FuncEval._provider_lock:
            failed = _FuncEval.provider_failures.get(key)
        if failed is not None:
            raise failed
        try:
            if inspect.isfunction(params):
                return params()
            return getattr(params.__self__, params.__name__)()
        except Exception as e:
            error = TestJunkieExecutionError(
                "parameters function '{name}' raised an unexpected error: {err}. See documentation: {link}".format(
                    name=getattr(params, '__name__', repr(params)), err=e,
                    link=DocumentationLinks.PARAMETERIZED_TESTS))
            error.__cause__ = e
            error.provider_traceback = traceback.format_exc()
            with _FuncEval._provider_lock:
                _FuncEval.provider_failures[key] = error
            raise error from e


class SuiteObject(object):

    def __init__(self, suite_definition):

        self.__suite_definition = suite_definition
        self.__listener = suite_definition["test_listener"](class_meta=suite_definition["class_meta"])
        self.__tests = []
        self.__test_function_names = []  # this suite has tests with those function names
        self.__test_components = set()  # this suite has tests that address those components
        self.__test_tags = []  # this suite has tests that are tagged with those tags
        self.__test_function_objects = []
        for test in suite_definition["suite_definition"].get(DecoratorType.TEST_CASE):
            test_obj = TestObject(test, self)
            self.__tests.append(test_obj)
            self.__test_function_names.append(test_obj.get_function_name())
            self.__test_function_objects.append(test_obj.get_function_object())
            self.__test_components.add(test_obj.get_component())
            self.__test_tags += test_obj.get_tags()
        self.__test_tags, self.__test_function_objects = set(self.__test_tags), set(self.__test_function_objects)
        self.metrics = ClassMetrics()
        self.__rules = suite_definition["test_rules"](suite=copy.deepcopy(self))
        self.__instance = None

    def get_suite_id(self):
        return self.get_kwargs().get("testjunkie_suite_id", 0)

    def get_decorated_definition(self, decorator_type):

        return self.__suite_definition["suite_definition"].get(decorator_type)

    def get_test_count(self):

        return len(self.__tests)

    def get_class_name(self):

        return self.__suite_definition["class_name"]

    def get_class_instance(self):

        if self.__instance is None:
            self.__instance = self.__suite_definition["class_object"]()
        return self.__instance

    def get_class_object(self):

        return self.__suite_definition["class_object"]

    def get_class_module(self):

        return self.get_class_object().__module__

    def update_test_objects(self, tests):

        self.__tests = tests

    def get_test_objects(self):
        """
        Use to get all TJ TestObjects
        :return: LIST of TestObjects
        """
        return self.__tests

    def get_test_function_names(self):
        """
        Use to get actual names of the test functions
        :return: LIST of STRINGS
        """
        return self.__test_function_names

    def get_test_components(self):
        """
        Use to get all the components that are covered by tests in this suite
        :return: LIST of STRINGS
        """
        return self.__test_components

    def get_test_tags(self):
        """
        Use to get all the tags that are covered by tests in this suite
        :return: LIST of STRINGS
        """
        return self.__test_tags

    def get_skip(self):
        return self.__suite_definition.get("class_skip", False)

    def can_skip(self, settings):
        """
        This function determines if the whole suite needs to be skipped.
        - if user asked to run tests for specific feature, it will check to make sure this suite matches that feature
        - if user asked to run tests for specific container, it will check to make sure suite has related tests
        - if user asked to run specific tags, it will verify that suite has tests with those tags
        - If user asked to run specific tests, it will check to make sure suite has that test
        :param settings: Settings object
        :return: If suite qualifies, it will return False, other wise it will return True.
        """
        def __all_tags_match(expected, actual):

            for _tag in expected:
                if _tag not in actual:
                    return False
            return True

        can_skip = _FuncEval.eval_skip(self)

        if settings.features is not None and can_skip is False:
            can_skip = not self.get_feature() in settings.features

        if settings.components is not None and can_skip is False:
            for component in settings.components:
                if component in self.get_test_components():
                    return False
            return True

        if settings.tags is not None and can_skip is False:

            if settings.tags.get("run_on_match_any", None) is not None:
                for tag in settings.tags["run_on_match_any"]:
                    if tag in self.get_test_tags():
                        return False
                return True

            if settings.tags.get("run_on_match_all", None) is not None:
                for test_obj in self.get_test_objects():
                    if __all_tags_match(expected=settings.tags["run_on_match_all"], actual=test_obj.get_tags()):
                        return False
                return True

        if settings.tests is not None and can_skip is False:
            names = self.get_test_function_names()
            names = names + ["{}.{}".format(self.get_class_name(), name) for name in names]
            for test in settings.tests:
                if inspect.ismethod(test) or inspect.isfunction(test):
                    test = test.__name__
                # names, Suite.test names or patterns like login_* (tj run -t)
                if isinstance(test, str) and any(fnmatch.fnmatchcase(name, test) for name in names):
                    return False
            return True

        return can_skip

    retry_override = None  # set by Runner.run() for tj run --no-retry, cleared when the run ends

    def get_retry_limit(self):

        if self.retry_override is not None:
            return self.retry_override
        return self.__suite_definition.get("class_retry", 1)

    def get_rules(self):

        return self.__rules

    def get_listener(self):

        return self.__listener

    def get_meta(self, copy_of_meta=False, class_parameter=_DECLARED):
        """
        :param class_parameter: leave out for the declared @Suite(meta=...) only; pass a suite parameter (None
                                included) for the declared meta plus what Meta.suite.update() set for it
        """
        declared = self.__suite_definition.get("class_meta", {})
        if class_parameter is _DECLARED:
            return copy.deepcopy(declared) if copy_of_meta else declared
        from test_junkie.views import META_LOCK
        with META_LOCK:
            merged = copy.deepcopy(declared) if copy_of_meta else dict(declared)
            merged.update(copy.deepcopy(self.__dict__.get("_SuiteObject__runtime_meta", {})
                                        .get(param_key(class_parameter), {})))
            return merged

    def update_runtime_meta(self, class_parameter, values):
        """Meta.suite.update(): suite-level values for one suite parameter."""
        from test_junkie.views import META_LOCK
        with META_LOCK:
            self.__dict__.setdefault("_SuiteObject__runtime_meta", {}) \
                .setdefault(param_key(class_parameter), {}).update(values)

    def get_unsuccessful_tests(self):

        unsuccessful_tests = []
        for test in self.get_test_objects():  # keeps the suite's test order (a set() used to scramble retries)
            if test not in unsuccessful_tests and any(value["status"] in TestCategory.ALL_UN_SUCCESSFUL
                                                      for metrics in test.metrics.get_metrics().values()
                                                      for value in metrics.values()):
                unsuccessful_tests.append(test)
        return unsuccessful_tests

    def has_unsuccessful_tests(self):

        tests = self.get_test_objects()
        for test in tests:
            for class_param, metrics in test.metrics.get_metrics().items():
                for value in metrics.values():
                    if value["status"] in TestCategory.ALL_UN_SUCCESSFUL:
                        return True
        return False

    def get_status(self):

        return self.metrics.get_metrics()["status"]

    def get_owner(self):

        return self.get_kwargs().get("owner", None)

    def get_parallel_restrictions(self):

        kwargs = self.get_kwargs()
        return kwargs.get("conflicts_with", kwargs.get("pr", []))

    def get_parameters(self, process_functions=False):
        if process_functions:
            parameters = self.__suite_definition["class_parameters"]
            eval_result = _FuncEval.eval_params(parameters)
            if eval_result is not None:
                self.__suite_definition["class_parameters"] = eval_result
            register_ids(self.__suite_definition["class_parameters"], self.get_kwargs().get("ids"))
        return self.__suite_definition["class_parameters"]

    def get_kwargs(self):

        return self.__suite_definition["decorator_kwargs"]

    def is_parallelized(self):

        return self.__suite_definition["parallelized"]

    def get_feature(self):

        return self.get_kwargs().get("feature", None)

    def get_priority(self):

        return self.get_kwargs().get("priority", None)

    def get_order(self):

        return self.get_kwargs().get("order", None)

    def get_runtime(self):

        return self.metrics.get_metrics().get("runtime", None)

    def get_number_of_actual_retries(self):

        return self.metrics.get_metrics().get("retry", 0)

    def get_data_by_tags(self):

        data = {"_totals_": Aggregator.get_template()}
        for test in self.get_test_objects():
            test_metrics = test.metrics.get_metrics()
            if test.get_tags():
                for tag in test.get_tags():
                    if tag not in data:
                        data.update({tag: Aggregator.get_template()})
                    Aggregator._update_report(data, test_metrics, tag)
            else:
                if None not in data:
                    data.update({None: Aggregator.get_template()})
                Aggregator._update_report(data, test_metrics, None)
        return data


class TestObject(object):

    def __init__(self, test_definition, suite):

        self.__test_definition = test_definition
        self.suite = suite
        self.metrics = TestMetrics()
        # run-time metadata, kept apart from the declared @test(meta=...): the live values per suite parameter /
        # parameter (declared + updates, carried across retries), and what each attempt set (latest per key)
        self.__meta_slots = {}
        self.__meta_attempts = {}

    def __repr__(self):
        return "<{}.{}>".format(self.suite.get_class_name(), self.get_function_name())

    def __deepcopy__(self, memo):
        """
        Copies the test's own definition (tags, meta, parameters, ...). The suite is NOT copied unless it's the one
        being copied (then the copy points at the suite copy): copying a test used to drag in its suite, every other
        test and all their metrics, which made each Rules hook call O(suite size) and a run O(N^2).
        Metrics are shared, same as TestMetrics.__deepcopy__ always did.
        """
        clone = TestObject.__new__(TestObject)
        memo[id(self)] = clone
        clone.__test_definition = copy.deepcopy(self.__test_definition, memo)
        clone.suite = memo.get(id(self.suite), self.suite)
        clone.metrics = self.metrics
        clone.__meta_slots = copy.deepcopy(self.__meta_slots, memo)
        clone.__meta_attempts = copy.deepcopy(self.__meta_attempts, memo)
        return clone

    def get_test_id(self):
        return self.get_kwargs().get("testjunkie_test_id", 0)

    def get_suite_id(self):
        # @test() runs before its class's @Suite() bumps the id counter, so the id recorded on the test was the
        # *previous* suite's - ask the suite instead
        return self.suite.get_suite_id()

    def get_skip(self):
        return self.get_kwargs().get("skip", False)

    def can_skip(self):
        return _FuncEval.eval_skip(self)

    def skip_before_test_rule(self):
        return self.get_kwargs().get("skip_before_test_rule", False)

    def skip_before_test(self):
        return self.get_kwargs().get("skip_before_test", False)

    def skip_after_test_rule(self):
        return self.get_kwargs().get("skip_after_test_rule", False)

    def skip_after_test(self):
        return self.get_kwargs().get("skip_after_test", False)

    def get_owner(self):

        return self.get_kwargs().get("owner", None)

    def get_priority(self):

        return self.get_kwargs().get("priority", None)

    def get_parameters(self, process_functions=False):
        if process_functions:
            parameters = self.get_kwargs().get("parameters", [None])
            eval_result = _FuncEval.eval_params(parameters)
            if eval_result is not None:
                self.get_kwargs()["parameters"] = eval_result
            register_ids(self.get_kwargs().get("parameters"), self.get_kwargs().get("ids"))
        return self.get_kwargs().get("parameters", [None])

    retry_override = None  # set by Runner.run() for tj run --retry N / --no-retry, cleared when the run ends
    run_policy = None  # set by Runner.run() for tj run --retry-policy, cleared when the run ends

    def get_retry_limit(self):

        if self.retry_override is not None:
            return self.retry_override
        policy = self.get_retry_policy()
        if policy is not None:
            return policy.total_attempts() or 1
        return self.get_kwargs().get("retry", 1)

    def get_retry_policy(self):
        """
        The RetryPolicy this test retries with: @test(retry=Policy), else @Suite(retry_policy=), else the run's
        --retry-policy. None for a test that sets retry=N.
        """
        if "_TestObject__retry_policy" not in self.__dict__:
            from test_junkie.retry import resolve
            retry = self.get_kwargs().get("retry")
            if retry is None or isinstance(retry, int):
                retry = None if "retry" in self.get_kwargs() else self.suite.get_kwargs().get("retry_policy")
            self.__retry_policy = resolve(retry, "@test(retry=...)")
        if self.__retry_policy is None and "retry" not in self.get_kwargs():
            return self.run_policy  # the run's --retry-policy, for tests that set nothing themselves
        return self.__retry_policy

    def get_function_name(self):

        return self.get_function_object().__name__

    def get_function_module(self):

        return self.get_function_object().__module__

    def get_function_object(self):

        return self.__test_definition["decorated_function"]

    def get_parallel_restrictions(self):

        kwargs = self.get_kwargs()
        return kwargs.get("conflicts_with", kwargs.get("pr", []))

    def get_tags(self):

        return self.get_kwargs().get("tags", [])

    def get_meta(self, parameter=None, class_parameter=None, copy_of_meta=False):
        """
        :return: DICT, the metadata of one parameter / suite parameter combination: the declared @test(meta=...)
                 plus everything Meta.update() set so far (across retries). The live dict unless copy_of_meta
        """
        from test_junkie.views import META_LOCK
        with META_LOCK:
            by_param = self.__meta_slots.setdefault(param_key(class_parameter), {})
            key = param_key(parameter)
            if key not in by_param:
                by_param[key] = copy.deepcopy(self.get_kwargs().get("meta") or {})
            return copy.deepcopy(by_param[key]) if copy_of_meta else by_param[key]

    def set_meta(self, parameter, class_parameter, values, attempt=None):
        """
        Update one combination's metadata, and record the values against the attempt that set them.
        :param attempt: INT, 1-based run of that combination; None works it out from the runs recorded so far
        """
        from test_junkie.views import META_LOCK
        with META_LOCK:
            self.get_meta(parameter, class_parameter).update(values)
            self.__attempt_record(parameter, class_parameter, attempt).update(values)

    def append_meta(self, parameter, class_parameter, key, items, attempt=None, call="Meta.append()", unique=False):
        """
        Add items to the list under one key of a combination's metadata (Meta.append / Meta.link / Meta.attach).
        The attempt's record lists the items added in that attempt.
        :param unique: leave out of the merged list an item it already has (Meta.link: a retry adding the same link
                       again shouldn't list it twice); the attempt's record still lists it
        :raises TestJunkieUsageError: the key already holds something other than a list
        """
        from test_junkie.errors import TestJunkieUsageError
        from test_junkie.views import META_LOCK
        with META_LOCK:
            values = self.get_meta(parameter, class_parameter)
            current = values.get(key)
            if current is None:
                current = []
            elif isinstance(current, tuple):
                current = list(current)
            elif not isinstance(current, list):
                raise TestJunkieUsageError(
                    "{call} adds to the list under {key!r}, but {key!r} already holds a {kind} ({value!r}). Use "
                    "another key, or Meta.update({key}=[...]) to replace it".format(
                        call=call, key=key, kind=type(current).__name__, value=current))
            added = [item for item in items if item not in current] if unique else list(items)
            values[key] = current + added  # a new list: the declared meta and earlier copies stay as they were
            record = self.__attempt_record(parameter, class_parameter, attempt)
            earlier = record.get(key)
            if earlier is None:
                record[key] = list(items)
            elif isinstance(earlier, list):
                record[key] = earlier + list(items)
            else:  # Meta.update() set a non-list there earlier in this attempt: record what the key holds now
                record[key] = list(values[key])

    def __attempt_record(self, parameter, class_parameter, attempt):
        """What one attempt set (caller holds META_LOCK). attempt None: the run after the ones recorded so far"""
        if attempt is None:
            data = self.metrics.get_metrics().get(param_key(class_parameter), {}).get(param_key(parameter), {})
            attempt = len(data.get("statuses") or []) + 1
        return self.__meta_attempts.setdefault(param_key(class_parameter), {}) \
            .setdefault(param_key(parameter), {}).setdefault(attempt, {})

    def get_meta_attempts(self, parameter=None, class_parameter=None):
        """
        :return: LIST of {"attempt": INT, "meta_set": DICT}, oldest first: what Meta.update() set in each run of
                 that combination (the latest value per key). Runs that set nothing aren't listed
        """
        from test_junkie.views import META_LOCK
        with META_LOCK:
            by_attempt = self.__meta_attempts.get(param_key(class_parameter), {}).get(param_key(parameter), {})
            return [{"attempt": n, "meta_set": copy.deepcopy(values)} for n, values in sorted(by_attempt.items())]

    def get_kwargs(self):

        return self.__test_definition["decorator_kwargs"]

    def get_no_retry_on(self):

        return self.get_kwargs().get("no_retry_on", [])

    def get_retry_on(self):

        return self.get_kwargs().get("retry_on", [])

    def get_component(self):

        return self.get_kwargs().get("component", None)

    def is_parallelized(self):

        return self.get_kwargs().get("parallelized", True)

    def parallelized_parameters(self):

        return self.get_kwargs().get("parallelized_parameters", False)

    def accepts_test_and_suite_parameters(self):

        return "parameter" in arg_names(self.get_function_object()) and \
               "suite_parameter" in arg_names(self.get_function_object())

    def accepts_test_parameters(self):

        return "parameter" in arg_names(self.get_function_object())

    def accepts_suite_parameters(self):

        return "suite_parameter" in arg_names(self.get_function_object())

    def __not_ran(self, param, class_param):
        """
        :param param: test parameter
        :param class_param: class parameter
        :return: BOOLEAN, True if test has not ran yet, False otherwise
        """
        return param_key(class_param) not in self.metrics.get_metrics() or \
            param_key(param) not in self.metrics.get_metrics()[param_key(class_param)]

    def is_qualified_for_retry(self, param=None, class_param=None):

        if self.__not_ran(param, class_param):
            return True
        test = self.metrics.get_metrics()[param_key(class_param)][param_key(param)]
        if test["status"] in TestCategory.ALL_UN_SUCCESSFUL:
            # subclasses count: retry_on=[requests.exceptions.Timeout] also retries ReadTimeout
            error = test["exceptions"][-1]
            policy = self.get_retry_policy()
            if policy is not None:
                return policy.qualifies(error)
            if self.get_no_retry_on() and isinstance(error, tuple(self.get_no_retry_on())):
                return False
            elif self.get_retry_on() and not isinstance(error, tuple(self.get_retry_on())):
                return False
            return True
        return False

    def get_status(self, param, class_param):

        if self.__not_ran(param, class_param):
            return None
        return self.metrics.get_metrics()[param_key(class_param)][param_key(param)]["status"]

    def get_number_of_actual_retries(self, param, class_param):

        if self.__not_ran(param, class_param):
            return 0
        return self.metrics.get_metrics()[param_key(class_param)][param_key(param)]["retry"]

    def is_flaky(self, parameter=None, suite_parameter=None):
        """
        True if this test, for these parameters, passed in the end after failing or erroring at least once in this
        run, whatever retried it: retry=N, a RetryPolicy or a suite retry pass
        """
        return self.metrics.is_flaky(parameter, suite_parameter)

    def get_flaky(self):
        """
        :return: LIST of {"parameter", "suite_parameter", "passed_on_run", "errors"}, one per parameter combination
                 that was flaky in this run. "errors" has what each failed run raised, as text, oldest first
        """
        from test_junkie.metrics import is_flaky
        flaky = []
        for by_param in self.metrics.get_metrics().values():
            for data in by_param.values():
                if is_flaky(data):
                    flaky.append({"parameter": data.get("param"), "suite_parameter": data.get("class_param"),
                                  "passed_on_run": len(data["statuses"]),
                                  "errors": ["{}: {}".format(type(error).__name__, error).split("\n")[0]
                                             for error in data.get("exceptions", [])[:-1] if error is not None]})
        return flaky


class _Pool(object):

    def __init__(self, name, max_concurrent, min_interval):
        self.name = name
        self.max_concurrent = max_concurrent
        self.min_interval = min_interval
        self.in_use = 0


class Limiter:
    """
    Global limits for a run. Set them in code before Runner.run(), or per run with Runner.run(...) / tj run flags,
    which take precedence for that run only.

    Truncation (what reports and the console keep of a failure):
        EXCEPTION_MESSAGE_LIMIT / EXCEPTION_MESSAGE_TRUNCATE - str(exception), e.g. "expected 200 but got 500"
        TRACEBACK_LIMIT / TRACEBACK_TRUNCATE                 - the formatted traceback, frames + the exception line
        *_TRUNCATE is TRUNCATE_TOP (cut the start, keep the end), TRUNCATE_BOTTOM (cut the end, keep the start) or
        TRUNCATE_MIDDLE (keep both ends, the default)

    Pacing (parallel runs):
        SUITE_THROTTLING / TEST_THROTTLING - at least this many seconds between two suite/test starts, run-wide
        RAMP_UP - seconds over which the suite and test thread limits grow from 1 to their full value
        pool() - named resource pools that tests and suites claim with uses=
    """

    # honor limits or not
    ACTIVE = True

    TRUNCATE_TOP = "top"
    TRUNCATE_BOTTOM = "bottom"
    TRUNCATE_MIDDLE = "middle"
    TRUNCATE_MODES = (TRUNCATE_TOP, TRUNCATE_BOTTOM, TRUNCATE_MIDDLE)

    # truncation limits
    __DEFAULT_LIMIT = 3000
    EXCEPTION_MESSAGE_LIMIT = __DEFAULT_LIMIT
    EXCEPTION_MESSAGE_TRUNCATE = TRUNCATE_MIDDLE
    TRACEBACK_LIMIT = __DEFAULT_LIMIT
    TRACEBACK_TRUNCATE = TRUNCATE_MIDDLE

    # throttling limits, seconds
    SUITE_THROTTLING = 0  # only applies to parallels
    TEST_THROTTLING = 0  # only applies to parallels
    RAMP_UP = 0

    # run setting -> Limiter attribute. Runner.run() kwargs, tj run flags and saved configs use the setting names
    SETTINGS = {"suite_throttling": "SUITE_THROTTLING", "test_throttling": "TEST_THROTTLING", "ramp_up": "RAMP_UP",
                "traceback_limit": "TRACEBACK_LIMIT", "message_limit": "EXCEPTION_MESSAGE_LIMIT",
                "truncate": ("TRACEBACK_TRUNCATE", "EXCEPTION_MESSAGE_TRUNCATE")}

    __LOCK = threading.Condition()
    __NEXT_START = {}  # gate -> earliest time.monotonic() the next start through it may happen
    __POOLS = {}  # name -> _Pool
    __TRUNCATED_TYPES = {}  # exception class -> subclass whose str() is the truncated message

    # ---------------------------------------------------------------------------------------------- truncation --

    @staticmethod
    def truncate(text, limit, mode=TRUNCATE_MIDDLE):
        """
        :param text: STRING
        :param limit: INT, how many characters of `text` to keep
        :param mode: STRING, Limiter.TRUNCATE_TOP, TRUNCATE_BOTTOM or TRUNCATE_MIDDLE
        :return: STRING, `text` if it fits, otherwise `limit` characters of it with a marker saying how much was cut
        """
        if not isinstance(text, str) or limit is None or limit < 0 or len(text) <= limit:
            return text
        cut = len(text) - limit
        if mode == Limiter.TRUNCATE_TOP:
            return "[. . . {:,} characters cut . . .]\n{}".format(cut, text[cut:])
        if mode == Limiter.TRUNCATE_BOTTOM:
            return "{}\n[. . . {:,} characters cut . . .]".format(text[:limit], cut)
        head = (limit + 1) // 2
        tail = limit - head
        return "{}\n[. . . {:,} characters cut . . .]\n{}".format(text[:head], cut,
                                                                 text[len(text) - tail:] if tail else "")

    @staticmethod
    def parse_exception_object(value):
        """
        :return: the exception, or a copy of it whose str() is truncated to EXCEPTION_MESSAGE_LIMIT. The copy is an
                 instance of a subclass named like the original, so isinstance(), retry_on and reports still see the
                 original type. The exception itself is never changed - listeners get it untouched
        """
        if not Limiter.ACTIVE or not isinstance(value, BaseException):
            return value
        try:
            message = str(value)
        except Exception:
            return value
        truncated = Limiter.truncate(message, Limiter.EXCEPTION_MESSAGE_LIMIT, Limiter.EXCEPTION_MESSAGE_TRUNCATE)
        if truncated is message:
            return value
        try:
            cls = type(value)
            sub = Limiter.__TRUNCATED_TYPES.get(cls)
            if sub is None:
                sub = type(cls.__name__, (cls,), {"__str__": lambda self: self._tj_message,
                                                  "__module__": cls.__module__})
                sub.__qualname__ = getattr(cls, "__qualname__", cls.__name__)
                Limiter.__TRUNCATED_TYPES[cls] = sub
            copied = sub.__new__(sub, *value.args)
            copied.__dict__.update(getattr(value, "__dict__", {}))
            copied._tj_message = truncated
            copied.__traceback__ = value.__traceback__
            copied.__cause__, copied.__context__ = value.__cause__, value.__context__
            return copied
        except Exception:  # a type that can't be subclassed or created like this: keep the original
            return value

    @staticmethod
    def parse_traceback(value):

        if Limiter.ACTIVE and isinstance(value, str):
            return Limiter.truncate(value, Limiter.TRACEBACK_LIMIT, Limiter.TRACEBACK_TRUNCATE)
        return value

    # ------------------------------------------------------------------------------------------------ pacing --

    @staticmethod
    def get_suite_throttling():
        return Limiter.SUITE_THROTTLING if Limiter.ACTIVE else 0

    @staticmethod
    def get_test_throttling(suite=None):
        """
        :param suite: SuiteObject, its @Suite(throttling=) wins over TEST_THROTTLING
        """
        if not Limiter.ACTIVE:
            return 0
        if suite is not None and suite.get_kwargs().get("throttling") is not None:
            return suite.get_kwargs()["throttling"]
        return Limiter.TEST_THROTTLING

    @staticmethod
    def get_ramp_up():
        return Limiter.RAMP_UP if Limiter.ACTIVE else 0

    @staticmethod
    def ramped(limit, elapsed):
        """
        :return: INT, the thread limit `elapsed` seconds into a run: grows from 1 to `limit` over RAMP_UP seconds
        """
        ramp = Limiter.get_ramp_up()
        if not ramp or limit <= 1 or elapsed >= ramp:
            return limit
        return max(1, min(limit, 1 + int((limit - 1) * elapsed / float(ramp))))

    @staticmethod
    def wait_turn(gate, interval, cancelled=None):
        """
        Waits for the next start through `gate`: starts through the same gate are at least `interval` seconds apart,
        across every thread. The first start doesn't wait. Each caller reserves its slot, so waiters go in order
        :param gate: hashable, e.g. "suite", "test", ("test", SuiteClass), ("pool", "grid")
        :param interval: NUMBER, seconds
        :param cancelled: callable returning True once the run is cancelled - stops waiting
        :return: BOOLEAN, False if the wait was cut short by a cancel
        """
        if not Limiter.ACTIVE or not interval:
            return True
        with Limiter.__LOCK:
            now = time.monotonic()
            start = max(now, Limiter.__NEXT_START.get(gate, now))
            Limiter.__NEXT_START[gate] = start + interval
        while True:
            remaining = start - time.monotonic()
            if remaining <= 0:
                return True
            if cancelled is not None and cancelled():
                return False
            time.sleep(min(remaining, 0.25))

    # -------------------------------------------------------------------------------------------------- pools --

    @staticmethod
    def pool(name, max_concurrent=None, min_interval=0):
        """
        Defines (or redefines) a resource pool that tests claim with @test(uses="name") or @Suite(uses="name")
        :param name: STRING
        :param max_concurrent: INT, how many tests may hold the pool at once. None: no cap
        :param min_interval: NUMBER, seconds between two tests starting with the pool
        """
        if not isinstance(name, str) or not name:
            raise BadParameters("Limiter.pool() needs a name, e.g. Limiter.pool(\"grid\", max_concurrent=5). "
                                "See documentation: {}".format(DocumentationLinks.RESOURCE_POOLS))
        if max_concurrent is not None and (isinstance(max_concurrent, bool) or not isinstance(max_concurrent, int)
                                           or max_concurrent < 1):
            raise BadParameters("Limiter.pool(\"{}\") max_concurrent must be a whole number of at least 1, or None. "
                                "See documentation: {}".format(name, DocumentationLinks.RESOURCE_POOLS))
        if isinstance(min_interval, bool) or not isinstance(min_interval, (int, float)) or min_interval < 0:
            raise BadParameters("Limiter.pool(\"{}\") min_interval must be 0 or more seconds. "
                                "See documentation: {}".format(name, DocumentationLinks.RESOURCE_POOLS))
        with Limiter.__LOCK:
            Limiter.__POOLS[name] = _Pool(name, max_concurrent, min_interval)
            return Limiter.__POOLS[name]

    @staticmethod
    def get_pools():
        """
        :return: DICT, pool name -> {"max_concurrent": ..., "min_interval": ..., "in_use": ...}
        """
        with Limiter.__LOCK:
            return {name: {"max_concurrent": pool.max_concurrent, "min_interval": pool.min_interval,
                           "in_use": pool.in_use} for name, pool in Limiter.__POOLS.items()}

    @staticmethod
    def remove_pools(*names):
        """
        Removes these pools, or every pool if no names are given
        """
        with Limiter.__LOCK:
            for name in (names or list(Limiter.__POOLS)):
                Limiter.__POOLS.pop(name, None)

    @staticmethod
    def pools_used(suite, test):
        """
        :return: LIST of pool names the test claims: its own uses= plus its suite's, sorted (the order they're taken)
        """
        names = set()
        for kwargs in (suite.get_kwargs(), test.get_kwargs()):
            uses = kwargs.get("uses")
            if uses:
                names.update([uses] if isinstance(uses, str) else uses)
        return sorted(names)

    @staticmethod
    def check_pools(suites):
        """
        Every uses= must name a pool defined with Limiter.pool() - checked before anything runs
        :param suites: LIST of SuiteObjects
        """
        with Limiter.__LOCK:
            known = set(Limiter.__POOLS)
        for suite in suites:
            for test in suite.get_test_objects():
                for kwargs, where in ((suite.get_kwargs(), "@Suite() of {}".format(suite.get_class_name())),
                                      (test.get_kwargs(), "@test() of {}.{}".format(suite.get_class_name(),
                                                                                    test.get_function_name()))):
                    uses = kwargs.get("uses")
                    for name in ([uses] if isinstance(uses, str) else uses or []):
                        if not isinstance(name, str):
                            raise BadParameters("uses= in {} takes pool names, got {!r}. See documentation: {}"
                                                .format(where, name, DocumentationLinks.RESOURCE_POOLS))
                        if name not in known:
                            raise BadParameters("uses=\"{}\" in {}: there is no such pool. Define it before the run "
                                                "with Limiter.pool(\"{}\", max_concurrent=N). See documentation: {}"
                                                .format(name, where, name, DocumentationLinks.RESOURCE_POOLS))

    @staticmethod
    def acquire(names, cancelled=None):
        """
        Takes a slot in each pool, in name order so two tests can't each hold one pool the other waits for
        :param names: LIST of pool names, from pools_used()
        :param cancelled: callable returning True once the run is cancelled - stops waiting
        :return: LIST of the pools taken (pass it to release()), or None if a cancel stopped the wait
        """
        taken = []
        if not Limiter.ACTIVE:
            return taken
        for name in names:
            with Limiter.__LOCK:
                pool = Limiter.__POOLS.get(name)
                if pool is None:  # removed after check_pools(): nothing left to limit
                    continue
                while pool.max_concurrent is not None and pool.in_use >= pool.max_concurrent:
                    if cancelled is not None and cancelled():
                        Limiter.__release(taken)
                        return None
                    Limiter.__LOCK.wait(0.25)
                pool.in_use += 1
                taken.append(pool)
            if not Limiter.wait_turn(("pool", name), pool.min_interval, cancelled):
                Limiter.release(taken)
                return None
        return taken

    @staticmethod
    def release(taken):
        with Limiter.__LOCK:
            Limiter.__release(taken)

    @staticmethod
    def __release(taken):
        for pool in taken or []:
            pool.in_use = max(0, pool.in_use - 1)
        Limiter.__LOCK.notify_all()

    # ------------------------------------------------------------------------------------------- per-run state --

    @staticmethod
    def start_run(overrides=None):
        """
        Called by Runner.run(): applies that run's limits on top of the ones set in code, and resets the throttling
        gates so a run never waits on the previous one
        :param overrides: DICT, setting name (see SETTINGS) -> value
        :return: DICT, what to pass to end_run() to put the previous values back
        """
        overrides = overrides or {}
        Limiter.validate(overrides)
        previous = {}
        for setting, value in overrides.items():
            for attribute in Limiter.__attributes(setting):
                previous[attribute] = getattr(Limiter, attribute)
                setattr(Limiter, attribute, value)
        with Limiter.__LOCK:
            Limiter.__NEXT_START.clear()
            for pool in Limiter.__POOLS.values():
                pool.in_use = 0
        return previous

    @staticmethod
    def end_run(previous):
        for attribute, value in (previous or {}).items():
            setattr(Limiter, attribute, value)

    @staticmethod
    def __attributes(setting):
        attributes = Limiter.SETTINGS[setting]
        return attributes if isinstance(attributes, tuple) else (attributes,)

    @staticmethod
    def validate(settings):
        """
        :param settings: DICT, setting name (see SETTINGS) -> value. Raises BadParameters for a bad one
        """
        for setting, value in settings.items():
            if setting not in Limiter.SETTINGS:
                raise BadParameters("Unknown limit \"{}\". Use one of: {}"
                                    .format(setting, ", ".join(sorted(Limiter.SETTINGS))))
            if setting == "truncate":
                if value not in Limiter.TRUNCATE_MODES:
                    raise BadParameters("truncate must be one of: {}, got {!r}. See documentation: {}"
                                        .format(", ".join(Limiter.TRUNCATE_MODES), value,
                                                DocumentationLinks.TRUNCATION))
            elif setting in ("traceback_limit", "message_limit"):
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise BadParameters("{} must be a whole number of characters, got {!r}. See documentation: {}"
                                        .format(setting, value, DocumentationLinks.TRUNCATION))
            elif isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise BadParameters("{} must be 0 or more seconds, got {!r}. See documentation: {}"
                                    .format(setting, value, DocumentationLinks.THROTTLING))


class GroupRulesObject(object):
    """
    Runs @beforeGroup / @afterGroup for the groups a suite belongs to. Suites can run in parallel, so each group's
    state is kept under one lock: the first member to arrive runs the group's @beforeGroup hooks (in definition order)
    while the others wait for the outcome, and @afterGroup runs once, after the last member.

    Every member reports when it's done (run_after_group), whether it ran, was skipped, ignored or cancelled.
    @afterGroup then runs if the group started: its @beforeGroup ran (passed or failed), or, for a group without
    one, a member got as far as running. A group whose members were all skipped never runs @afterGroup.
    """

    _PENDING, _RUNNING, _DONE, _FAILED = "pending", "running", "done", "failed"

    def __init__(self, definition):

        self.definition = definition
        self.__lock = threading.Lock()
        # group -> {"before": state, "failure": dict or None, "finished": threading.Event(), "started": bool}
        self.__state = {group: self.__new_state() for group in definition}

    def __new_state(self):
        return {"before": self._PENDING, "failure": None, "finished": threading.Event(), "started": False}

    def mark_started(self, suite):
        """The suite is about to run its tests: its groups count as started even without a @beforeGroup"""
        with self.__lock:
            for group, definition in self.definition.items():
                if suite.get_class_object() in definition["suites"]:
                    self.__state.setdefault(group, self.__new_state())["started"] = True

    def run_after_group(self, suite):

        to_run = []
        with self.__lock:
            for group, definition in self.definition.items():
                if suite.get_class_object() in definition["suites"]:
                    definition["suites"].remove(suite.get_class_object())
                    started = self.__state.setdefault(group, self.__new_state())["started"]
                    if not definition["suites"] and started and DecoratorType.AFTER_GROUP in definition["rules"]:
                        to_run.extend(definition["rules"].pop(DecoratorType.AFTER_GROUP))
        for func in to_run:
            try:
                func["decorated_function"]()
            except Exception as error:
                trace = traceback.format_exc()
                return {"trace": trace, "exception": error}
        return None

    def run_before_group(self, suite, rule_type):
        """
        :return: None if every group's @beforeGroup passed, else {group: {"trace", "exception", "definition",
                 "first"}} for the first group that failed. "first" is True only for the suite that ran the hook,
                 so listener events fire once per failure.
        """
        for group, definition in self.definition.items():
            if suite.get_class_object() not in definition["suites"] or rule_type not in definition["rules"]:
                continue
            with self.__lock:
                state = self.__state.setdefault(group, self.__new_state())
                owner = state["before"] == self._PENDING
                if owner:
                    state["before"] = self._RUNNING
                    state["started"] = True
            if owner:
                failure = None
                try:
                    for func in list(definition["rules"][rule_type]):
                        try:
                            func["decorated_function"]()
                        except Exception as error:  # the rest of the group's hooks are skipped
                            failure = {"trace": traceback.format_exc(), "exception": error, "definition": definition}
                            break
                except BaseException as error:  # sys.exit() etc.: fail the group for the waiters, then re-raise
                    failure = {"trace": traceback.format_exc(), "exception": error, "definition": definition}
                    raise
                finally:
                    with self.__lock:
                        state["failure"] = failure
                        state["before"] = self._FAILED if failure else self._DONE
                    state["finished"].set()
                if failure:
                    return {group: dict(failure, first=True)}
            else:
                state["finished"].wait()
                if state["failure"]:
                    return {group: dict(state["failure"], first=False)}
        return None
