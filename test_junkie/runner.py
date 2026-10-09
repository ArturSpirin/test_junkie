import copy
import fnmatch
import os
import random
import signal
import threading
import time
import traceback
from test_junkie.console import Capture, Console, Router, RunState, TestInterrupted, capturing, unit_key
from test_junkie.constants import SuiteCategory, TestCategory, Event, DocumentationLinks, TestOrder, Undefined
from test_junkie.debugger import LogJunkie
from test_junkie.decorators import DecoratorType, synchronized
from test_junkie.errors import ConfigError, TestJunkieExecutionError, TestListenerError, BadParameters, SkipTest
from test_junkie.listener import Listener
from test_junkie.metrics import Aggregator, ResourceMonitor
from test_junkie.objects import Limiter, arg_names, _FuncEval
from test_junkie.parallels import ParallelProcessor
from test_junkie.rerun import parameters_to_run
from test_junkie.builder import Builder
from test_junkie.reporter.xml_reporter import XmlReporter
from test_junkie.rules import Rules
from test_junkie.settings import Settings
from test_junkie.views import TestView

# shared lock for __process_event() - can't create it inline there, @synchronized() would just
# get a new Lock() every call
_EVENT_PROPERTIES_LOCK = threading.Lock()


# Event -> name of the Listener hook that handles it
_EVENT_HANDLERS = {Event.ON_SUCCESS: "on_success", Event.ON_FAILURE: "on_failure", Event.ON_ERROR: "on_error",
                   Event.ON_SKIP: "on_skip", Event.ON_CANCEL: "on_cancel", Event.ON_IGNORE: "on_ignore",
                   Event.ON_IN_PROGRESS: "on_in_progress", Event.ON_COMPLETE: "on_complete",
                   Event.ON_RETRY: "on_retry",
                   Event.ON_CLASS_CANCEL: "on_class_cancel", Event.ON_CLASS_SKIP: "on_class_skip",
                   Event.ON_BEFORE_CLASS_ERROR: "on_before_class_error",
                   Event.ON_BEFORE_CLASS_FAIL: "on_before_class_failure",
                   Event.ON_CLASS_IGNORE: "on_class_ignore", Event.ON_AFTER_CLASS_ERROR: "on_after_class_error",
                   Event.ON_AFTER_CLASS_FAIL: "on_after_class_failure",
                   Event.ON_CLASS_IN_PROGRESS: "on_class_in_progress",
                   Event.ON_BEFORE_GROUP_FAIL: "on_before_group_failure",
                   Event.ON_BEFORE_GROUP_ERROR: "on_before_group_error",
                   Event.ON_AFTER_GROUP_FAIL: "on_after_group_failure",
                   Event.ON_AFTER_GROUP_ERROR: "on_after_group_error",
                   Event.ON_CLASS_COMPLETE: "on_class_complete"}
_NATIVE_LISTENER = Listener()


class _RunContext(object):
    """
    What a test needs from the run it belongs to: cancel state, the console and the output router
    """

    def __init__(self, state, console, router, cancel_by_user):
        self.state = state
        self.console = console
        self.router = router
        self.cancel_by_user = cancel_by_user


class Runner:

    __STATS = {}

    def __init__(self, suites, **kwargs):

        if not suites or not isinstance(suites, list):
            raise BadParameters("Runner needs to be initiated with a mandatory argument \"suites\" which must be of "
                                "type {} and it can not be empty. Instead got: {}. Please see documentation: {}"
                                .format(list, suites, DocumentationLinks.RUNNER_OBJECT))

        self.__stats = {}
        # TestOrder.RANDOM shuffles with this seed - the run header prints it, tj run --seed repeats an order
        self.seed = kwargs.get("seed")
        if self.seed is None or self.seed is Undefined:
            self.seed = random.randrange(1, 1000000)
        kwargs["seed"] = self.seed
        rng = random.Random(self.seed)

        self.__all_suites = self.__prioritize(suites=suites)
        for suite in self.__all_suites:
            suite_object = Builder.get_execution_roster().get(suite, None)
            suite_object.update_test_objects(self.__prioritize(suite_object=suite_object, rng=rng))
            Runner.__process_owners(suite_object)

        self.__kwargs = kwargs
        self.__settings = None
        self.__processor = None

        self.__suites = []
        self.__cancel = False
        self.__state = None
        self.exit_code = None
        self.__executed_suites = []
        self.__active_suites = []
        # built here too so a bad @beforeGroup/@afterGroup definition still raises when the Runner is created
        self.__group_rules = Builder.build_group_definitions(self.__all_suites)
        self.__before_group_failure_records = {}

    def __reset_for_run(self):
        """
        Everything run() consumes or accumulates, so the same Runner can be run again
        """
        self.__suites = list(self.__all_suites)  # run() removes suites from this list as it goes
        # not resetting __cancel here - cancel() before run() is supported; run() clears it when it ends
        self.__executed_suites = []
        self.__active_suites = []
        self.__before_group_failure_records = {}
        self.__thread_errors = []
        self.__changed_parameters = set()  # tests a rerun runs with all parameters, already reported
        self.__group_rules = Builder.build_group_definitions(self.__all_suites)
        for suite in self.__all_suites:
            suite_object = Builder.get_execution_roster().get(suite, None)
            # suites/tests are singletons, so reset metrics or a rerun just reuses old statuses (fixes ticket: #43)
            suite_object.metrics.reset()
            for test_object in suite_object.get_test_objects():
                test_object.metrics.reset()

    @staticmethod
    def __process_owners(suite_object):

        tests = suite_object.get_test_objects()
        for test in tests:
            if test.get_owner() is None:
                test.get_kwargs().update({"owner": suite_object.get_owner()})

    @staticmethod
    def __prioritize(suites=None, suite_object=None, rng=random):
        """
        Orders suites or the tests within a suite for execution.

        When called with suite_object, the suite's @Suite(order=) value controls test ordering:
          - TestOrder.ALPHABETICAL  : sort tests by function name
          - TestOrder.RANDOM        : shuffle tests (random.shuffle)
          - TestOrder.PRIORITY_ASC  : explicit numeric priority ascending (default)
          - TestOrder.PRIORITY_DESC : explicit numeric priority descending
        Tests without a numeric priority always trail prioritized tests in both ASC and DESC modes.

        :param suites: LIST of class objects decorated with @Suite  (suite-level ordering)
        :param suite_object: SuiteObject                             (test-level ordering)
        :return: LIST ordered accordingly
        """
        items = suites if suites is not None else suite_object.get_test_objects()
        order = suite_object.get_order() if suite_object is not None and suites is None else None

        if order is not None:
            _valid = {TestOrder.RANDOM, TestOrder.ALPHABETICAL, TestOrder.PRIORITY_ASC, TestOrder.PRIORITY_DESC}
            if order not in _valid:
                raise BadParameters(
                    "Invalid value '{}' for 'order' argument in @Suite() decorator. "
                    "Expected one of: {}. See documentation: {}".format(
                        order, sorted(_valid), DocumentationLinks.SUITE_DECORATOR))

        if order == TestOrder.RANDOM:
            # shuffle from declaration order, not from the current list (an earlier run in this process may have
            # shuffled it already) - so the same seed always gives the same order
            def declared(test):
                code = getattr(test.get_function_object(), "__code__", None)
                return (code.co_firstlineno if code is not None else 0), test.get_function_name()
            result = sorted(items, key=declared)
            rng.shuffle(result)
            return result

        if order == TestOrder.ALPHABETICAL:
            return sorted(items, key=lambda t: t.get_function_name())

        reverse = order == TestOrder.PRIORITY_DESC

        ordered = []
        priorities = {}
        no_priority = []
        not_parallelized = []

        for item in items:
            if suites is not None:
                _so = Builder.get_execution_roster().get(item, None)
                if _so is None:
                    raise BadParameters(
                        "{} was passed to Runner but is not registered as a test suite. "
                        "Ensure the class is decorated with @Suite() and was imported before Runner was "
                        "constructed. See documentation: {}".format(item, DocumentationLinks.SUITE_DECORATOR))
                priority = _so.get_priority()
                is_parallelized = _so.is_parallelized()
            else:
                priority = item.get_priority()
                is_parallelized = item.is_parallelized()

            if priority is None:
                if is_parallelized:
                    no_priority.append(item)
                else:
                    not_parallelized.append(item)
            else:
                if priority not in priorities:
                    priorities[priority] = [item]
                else:
                    priorities[priority].append(item)

        for priority in sorted(priorities.keys(), reverse=reverse):
            ordered.extend(priorities[priority])

        ordered += no_priority + not_parallelized
        return ordered

    def get_executed_suites(self):
        """
        :return: LIST of SuiteObjects that begun executing
        """
        return self.__executed_suites

    def cancel(self):
        """
        Flips the switch to cancel the execution of tests: nothing new starts and nothing is retried, tests already
        running finish
        :return: None
        """
        self.__cancel = True
        if self.__state is not None:
            self.__state.cancelled = True

    def __cancel_by_user(self):
        """
        Ctrl+C, or a KeyboardInterrupt raised in a test
        """
        state = self.__state
        if state is None or state.by_user:
            return
        state.cancelled = True
        state.by_user = True
        self.__context.console.cancelling()

    def __on_interrupt(self, signum, frame):
        state = self.__state
        state.interrupts += 1
        if state.interrupts > 1:
            self.__context.console.force_stop()
            os._exit(130)
        self.__cancel_by_user()
        if state.main_thread_in_test:  # a sequential run: stop the test that's running right now
            raise TestInterrupted()

    def run(self, **kwargs):
        """
        Initiates the execution process that runs tests
        :return: Aggregator with the run's results, e.g. run().get_basic_report()
        """
        self.__reset_for_run()
        self.__settings = Settings(runner_kwargs=self.__kwargs, run_kwargs=kwargs)
        cli = self.__settings.kwargs.get("_cli")  # set by tj run: sources and scan time for the header
        mode = ("cli-quiet" if cli else "silent") if self.__settings.quiet else "normal"
        state = self.__state = RunState(cancelled=self.__cancel)  # cancel() before run() is supported
        console = Console(self.__settings, mode=mode, cli=cli, state=state)
        router = Router(console, capture_enabled=self.__settings.capture or self.__settings.quiet)
        self.__context = _RunContext(state, console, router, self.__cancel_by_user)
        initial_start_time = time.time()
        resource_monitor = None
        run_error = None
        previous_handler = None
        objects = [Builder.get_execution_roster()[suite] for suite in self.__all_suites]
        objects += [test for suite in objects for test in suite.get_test_objects()]
        Limiter.check_pools([Builder.get_execution_roster()[suite] for suite in self.__suites])
        _FuncEval.provider_failures.clear()
        limits = Limiter.start_run(self.__settings.limits)  # put back in the finally at the end of run()
        retry = self.__settings.retry
        for item in objects:  # tj run --retry N / --no-retry, for this run only
            item.retry_override = None if retry is None else (retry if hasattr(item, "get_function_name") else
                                                              (1 if retry == 1 else None))
        rerun = self.__settings.rerun
        if rerun is not None:  # suites with nothing to run again are not part of this run
            self.__suites = [suite for suite in self.__suites if any(
                rerun.includes_test(test.suite.get_class_name(), test.get_function_name())
                for test in Builder.get_execution_roster()[suite].get_test_objects())]
        router.install()
        if threading.current_thread() is threading.main_thread():
            try:
                if signal.getsignal(signal.SIGINT) is signal.default_int_handler:  # leave a custom handler alone
                    previous_handler = signal.signal(signal.SIGINT, self.__on_interrupt)
            except (ValueError, OSError):
                previous_handler = None
        try:
            if self.__settings.monitor_resources:
                resource_monitor = ResourceMonitor()
                resource_monitor.start()
            self.__processor = ParallelProcessor(self.__settings)
            console.start([Builder.get_execution_roster()[suite] for suite in self.__suites])

            try:
                while self.__suites:
                    generation = ParallelProcessor.generation()
                    for suite in list(self.__suites):
                        # never missing - Runner() already rejected anything that isn't a registered suite
                        suite_object = Builder.get_execution_roster()[suite]
                        if state.cancelled:  # nothing to wait for - the suite is just marked cancelled
                            self.__executed_suites.append(suite_object)
                            self.__run_suite(suite_object)
                            self.__suites.remove(suite)
                        elif self.__processor.suite_multithreading() and suite_object.is_parallelized():
                            while True:
                                suite_generation = ParallelProcessor.generation()
                                if self.__processor.suite_qualifies(suite_object):
                                    Limiter.wait_turn("suite", Limiter.get_suite_throttling(), state)
                                    self.__executed_suites.append(suite_object)
                                    ParallelProcessor.run_suite_in_a_thread(
                                        self.__capture_thread_errors(self.__run_suite), suite_object)
                                    self.__suites.remove(suite)
                                    break
                                elif suite_object.get_priority() is None:
                                    break
                                else:  # a prioritized suite holds its place until a running suite finishes
                                    ParallelProcessor.wait_for_change(suite_generation)
                        else:
                            if not suite_object.is_parallelized():
                                LogJunkie.debug("Cant run suite: {} in parallel with any other suites. Waiting for "
                                                "parallel suites to finish so I can run it by itself."
                                                .format(suite_object.get_class_object()))
                                ParallelProcessor.wait_currently_active_suites_to_finish()
                            self.__executed_suites.append(suite_object)
                            self.__run_suite(suite_object)
                            self.__suites.remove(suite)
                    LogJunkie.debug("{} Suite(s) left in queue.".format(len(self.__suites)))
                    if self.__suites and not state.cancelled:  # the rest wait on running suites
                        ParallelProcessor.wait_for_change(generation)
            except KeyboardInterrupt:
                # raised outside of a test (no Ctrl+C handler on this thread, or a hook raised it): suites that
                # didn't start are counted as cancelled
                self.__cancel_by_user()

            ParallelProcessor.wait_currently_active_suites_to_finish()
        except Exception as error:
            # report on what did run before raising - used to exit without the summary or the HTML/XML reports
            run_error = error
            ParallelProcessor.wait_currently_active_suites_to_finish()
        finally:
            if resource_monitor is not None:  # is None if ResourceMonitor() itself failed - don't mask that error
                resource_monitor.shutdown()

        errors = ([run_error] if run_error is not None else []) + self.__thread_errors
        listener_errors = [error for suite in self.get_executed_suites()
                           for error in suite.metrics.get_listener_errors()]
        if listener_errors:
            first = listener_errors[0]
            listener_error = TestListenerError(
                "{} listener call{} failed, first: {}.{}: {!r}. For help on defining custom event listeners, see "
                "documentation: {}".format(len(listener_errors), "" if len(listener_errors) == 1 else "s",
                                           first["test"].suite.get_class_name() if first["test"] else "suite",
                                           first["event"], first["exception"], DocumentationLinks.LISTENERS))
            listener_error.listener_calls = len(listener_errors)
            errors.append(listener_error)
        for error in errors[1:]:
            LogJunkie.error("Another error in a suite/test thread: {!r}".format(error))

        runtime = time.time() - initial_start_time
        aggregator = Aggregator(self.get_executed_suites())
        try:
            try:
                self.exit_code = console.finish(aggregator, runtime, errors,
                                                resources=resource_monitor.samples if resource_monitor else None)
            finally:
                router.uninstall()
                if previous_handler is not None:
                    signal.signal(signal.SIGINT, previous_handler)
            if self.__settings.html_report:
                from test_junkie.reporter.html_reporter import Reporter  # only loaded when a report is requested
                reporter = Reporter(monitoring_file=resource_monitor.get_file_path()
                                    if resource_monitor is not None else None,
                                    runtime=runtime,
                                    aggregator=aggregator,
                                    multi_threading_enabled=self.__processor.test_multithreading()
                                    or self.__processor.suite_multithreading())
                reporter.generate_html_report(self.__settings.html_report)
            XmlReporter.create_xml_report(write_file=self.__settings.xml_report, suites=self.get_executed_suites())
            if self.__settings.json_report:
                from test_junkie.reporter.json_reporter import write_json_report
                write_json_report(self.__settings.json_report, aggregator, runtime, self.seed)
        except Exception:
            if not errors:
                raise
            # the run already failed - that's the error to surface, not a report choking on the partial results
            LogJunkie.error("Reporting failed after the run failed: {}".format(traceback.format_exc()))
        finally:
            # needs to run even if reporting above throws or the temp file never gets removed
            if resource_monitor is not None:
                resource_monitor.cleanup()
            for item in objects:
                item.retry_override = None
            Limiter.end_run(limits)
            self.__cancel = False  # a cancel applies to the run it was requested for, not every later run()
        if errors:
            raise errors[0]  # same error as before, now raised after the summary and reports were written
        if state.by_user:
            interrupt = KeyboardInterrupt()
            interrupt.tj_reported = True  # the console already said it was cancelled
            raise interrupt
        return aggregator

    def __capture_thread_errors(self, func):
        """
        Wraps a suite/test thread target. An unexpected exception in a thread used to die with the thread: its
        unfinished tests vanished from the results and run() returned normally. run() now re-raises it once the
        threads are done, same as when the suite runs on the main thread.
        """
        def target(*args):
            try:
                func(*args)
            except BaseException as error:
                self.__thread_errors.append(error)
        return target

    @staticmethod
    def __needs_retry(test, class_param, parameters):
        """
        :return: BOOLEAN, True if any of these parameters still qualifies for a retry under this suite parameter
        """
        return any(test.is_qualified_for_retry(param, class_param=class_param) for param in parameters)

    def __parameters(self, test, class_param):
        """
        :return: LIST, the test's parameters to run under this suite parameter - all of them, unless this is a rerun
        """
        parameters = test.get_parameters(process_functions=True)
        rerun = self.__settings.rerun
        if rerun is None or not parameters or not isinstance(parameters, list):
            return parameters  # bad parameters are reported as usual
        chosen = parameters_to_run(rerun, test, parameters, test.suite.get_parameters(process_functions=True),
                                   class_param)
        if chosen is None:  # none of its parameters are in the rerun - they changed since, so all of them run
            if test not in self.__changed_parameters:
                self.__changed_parameters.add(test)
                self.__context.console.note("{}.{}: none of its parameters are in the rerun, running all of them"
                                            .format(test.suite.get_class_name(), test.get_function_name()))
            return parameters
        return chosen

    def __in_rerun(self, test, class_param):
        """
        :return: BOOLEAN, True if a rerun has something left to run for the test under this suite parameter
        """
        if not self.__settings.rerun.includes_test(test.suite.get_class_name(), test.get_function_name()):
            return False
        try:
            parameters = test.get_parameters(process_functions=True)
        except TestJunkieExecutionError:
            return True  # gets reported as bad parameters
        if not parameters or not isinstance(parameters, list):
            return True  # gets reported as bad parameters
        chosen = self.__parameters(test, class_param)
        if test.accepts_suite_parameters():
            return bool(chosen)
        # it runs once, under the first suite parameter - after that it has nothing left
        return any(test.get_status(param, None) is None for param in chosen)

    @staticmethod
    def __validate_suite_parameters(suite):
        try:
            parameters = suite.get_parameters(process_functions=True)
        except TestJunkieExecutionError as error:  # the parameters function raised: this suite is ignored, not the run
            return error
        if not parameters or not isinstance(parameters, list):
            if isinstance(parameters, list):
                return BadParameters("Argument: \"parameters\" in @Suite() decorator returned empty: <class 'list'>. "
                                     "For more info, see this explanation: {}"
                                     .format(DocumentationLinks.ON_CLASS_IGNORE))
            else:
                return BadParameters("Argument: \"parameters\" in @Suite() decorator must be of type: <class 'list'> "
                                     "but found: {}. For more info, see @Suite() decorator documentation: {}"
                                     .format(type(parameters), DocumentationLinks.SUITE_DECORATOR))
        return False

    @staticmethod
    def __validate_test_parameters(test):
        try:
            parameters = test.get_parameters(process_functions=True)
        except TestJunkieExecutionError as error:  # the parameters function raised: this test is ignored, not the run
            return {"exception": error, "trace": getattr(error, "provider_traceback", None) or str(error)}
        if not parameters or not isinstance(parameters, list):
            exception = None
            try:
                if isinstance(parameters, list):
                    exception = BadParameters("Argument: \"parameters\" in @test() decorator returned empty: "
                                              "<class 'list'>. For more info, see: {}"
                                              .format(DocumentationLinks.ON_TEST_IGNORE))
                else:
                    exception = BadParameters("Argument: \"parameters\" in @test() decorator must be of type: "
                                              "<class 'list'> but found: {}. For more info, see @test() decorator "
                                              "documentation: {}"
                                              .format(type(parameters), DocumentationLinks.TEST_DECORATOR))
                raise exception
            except:
                return {"exception": exception, "trace": traceback.format_exc()}

    def __run_suite(self, suite):

        context = self.__context
        capture = Capture()
        start_time = time.time()
        try:
            with capturing(context.router, capture):
                self.__run_suite_body(suite, context)
        except (TestInterrupted, KeyboardInterrupt):
            raise
        except BaseException as error:
            # something ended the suite early: report the tests it never got to as ignored instead of leaving them out
            self.__ignore_unfinished(suite, error, traceback.format_exc(), start_time)
            context.console.suite_finished(suite)
            raise
        finally:
            if capture.output() or capture.log:
                suite.metrics.record_output(capture.output(), capture.log)
        context.console.suite_finished(suite)

    def __ignore_unfinished(self, suite, error, trace, start_time):
        """
        Records every test of the suite that would have run but has no result yet as ignored, with the error that
        ended the suite
        """
        ParallelProcessor.wait_currently_active_tests_to_finish(suite)
        try:
            class_params = suite.get_parameters(process_functions=True)
        except Exception:
            class_params = None
        if not isinstance(class_params, list) or not class_params:
            class_params = [None]
        rerun = self.__settings.rerun
        for test in suite.get_test_objects():
            if self.__positive_skip_condition(test=test) or \
                    not Runner.__runnable_tags(test=test, tag_config=self.__settings.tags):
                continue
            if rerun is not None and not rerun.includes_test(suite.get_class_name(), test.get_function_name()):
                continue
            for class_param in class_params if test.accepts_suite_parameters() else class_params[:1]:
                try:
                    parameters = self.__parameters(test, class_param)
                except Exception:
                    continue
                if not isinstance(parameters, list):
                    continue
                for param in parameters:
                    Runner.__ignore_unit(self.__context, suite, test, param, class_param, error, trace)
        if suite.metrics.get_metrics()["status"] is None:
            suite.metrics.update_suite_metrics(status=SuiteCategory.FAIL, start_time=start_time)

    @staticmethod
    def __ignore_unit(context, suite, test, param, class_param, error, trace):
        """
        Records one test run that never got a result as ignored
        :param context: the run's _RunContext to update the console, None if the caller does that itself
        """
        recorded = class_param if test.accepts_suite_parameters() else None
        if test.get_status(param, recorded) is not None:
            return
        test.metrics.update_metrics(status=TestCategory.IGNORE, start_time=time.time(), param=param,
                                    class_param=recorded, exception=error, formatted_traceback=trace)
        Runner.__process_event(event=Event.ON_IGNORE, suite=suite, test=test, class_param=recorded, param=param,
                               error=error, formatted_traceback=trace)
        if context is not None:
            context.console.unit_done(suite, unit_key(test, param, class_param), TestCategory.IGNORE,
                                      Runner.__label(suite, test, param, class_param))

    def __run_suite_body(self, suite, context):
        try:
            self.__run_suite_steps(suite, context)
        finally:
            # every member reports in, however it ended: @afterGroup runs after the last one, if the group started
            after_group_failed = self.__group_rules.run_after_group(suite)
            if after_group_failed:
                event = Event.ON_AFTER_GROUP_FAIL if isinstance(after_group_failed["exception"],
                                                                AssertionError) else Event.ON_AFTER_GROUP_ERROR
                Runner.__process_event(event=event, suite=suite, error=after_group_failed["exception"],
                                       formatted_traceback=after_group_failed["trace"])

    def __run_suite_steps(self, suite, context):

        def before_group_rule_failed():
            for group, _result in self.__before_group_failure_records.items():
                if suite.get_class_object() in _result["definition"]["suites"]:
                    return _result["trace"]

        state = context.state
        suite_start_time = time.time()
        unsuccessful_tests = None
        # the skip check comes first: a skipped suite doesn't evaluate its parameters or set up its group
        skipped = suite.can_skip(self.__settings)
        exception = None
        if not skipped and not state.cancelled:
            exception = Runner.__validate_suite_parameters(suite)
        if not skipped and not state.cancelled and not exception:
            exception = before_group_rule_failed()
            if not exception:
                result = self.__group_rules.run_before_group(suite, DecoratorType.BEFORE_GROUP)
                if result is not None:
                    self.__before_group_failure_records.update(result)
                    failure = result[list(result.keys())[0]]
                    exception = failure["trace"]
                    if failure.get("first", True):  # once per failure, not once per waiting member
                        event = Event.ON_BEFORE_GROUP_FAIL if isinstance(failure["exception"], AssertionError) \
                            else Event.ON_BEFORE_GROUP_ERROR
                        Runner.__process_event(event=event, suite=suite, error=failure["exception"],
                                               formatted_traceback=failure["trace"])

        if not skipped and not state.cancelled and not exception:
            self.__group_rules.mark_started(suite)
            Runner.__process_event(event=Event.ON_CLASS_IN_PROGRESS, suite=suite)
            context.console.suite_started(suite)
            for suite_retry_attempt in range(1, suite.get_retry_limit() + 1):
                if suite_retry_attempt > 1 and state.cancelled:
                    break
                if suite_retry_attempt == 1 or suite.get_status() in SuiteCategory.ALL_UN_SUCCESSFUL:

                    for class_param in suite.get_parameters(process_functions=True):
                        LogJunkie.debug("Running suite: {}".format(suite.get_class_object()))
                        LogJunkie.debug("Suite Retry {}/{} with Param: {}"
                                        .format(suite_retry_attempt, suite.get_retry_limit(), class_param))

                        if suite_retry_attempt > 1:
                            unsuccessful_tests = suite.get_unsuccessful_tests()
                            LogJunkie.debug("There are {} unsuccessful tests that need to be retried"
                                            .format(len(unsuccessful_tests)))
                            # decided before @beforeClass - this used to run @beforeClass and then bail out
                            # without @afterClass when there was nothing left to retry for this suite parameter
                            tests = [test for test in unsuccessful_tests
                                     if Runner.__needs_retry(test, class_param,
                                                             self.__parameters(test, class_param))]
                            if not tests:
                                continue
                        else:
                            tests = list(suite.get_test_objects())
                            if self.__settings.rerun is not None:
                                # decided before @beforeClass, same as for a retry
                                tests = [test for test in tests if self.__in_rerun(test, class_param)]
                                if not tests:
                                    continue

                        before_class_error = Runner.__run_before_class(suite, class_param)

                        while tests:
                            for test in list(tests):

                                test_start_time = time.time()  # will use in case of a failure in context of this loop

                                if not self.__positive_skip_condition(test=test) and \
                                        Runner.__runnable_tags(test=test, tag_config=self.__settings.tags):

                                    if not test.is_parallelized() and not state.cancelled:
                                        LogJunkie.debug("Cant run test: {} in parallel with any other tests"
                                                        .format(test.get_function_object()))
                                        ParallelProcessor.wait_currently_active_tests_to_finish()

                                    bad_params = Runner.__validate_test_parameters(test)
                                    if bad_params is not None:
                                        tests.remove(test)
                                        test.metrics.update_metrics(status=TestCategory.IGNORE,
                                                                    start_time=test_start_time,
                                                                    exception=bad_params["exception"],
                                                                    formatted_traceback=bad_params["trace"])
                                        Runner.__process_event(event=Event.ON_IGNORE, suite=suite, test=test,
                                                               class_param=class_param, error=bad_params)
                                        context.console.unit_done(suite, unit_key(test, None, class_param),
                                                                  TestCategory.IGNORE, Runner.__label(suite, test))
                                        continue

                                    ParallelProcessor.wait_while(lambda: not state.cancelled and
                                                                 not self.__processor.test_qualifies(test))

                                    for param in self.__parameters(test, class_param):
                                        if unsuccessful_tests is not None and \
                                                not test.is_qualified_for_retry(param, class_param=class_param):
                                            # If does not qualify with current parameter, will move to the next
                                            continue
                                        if not state.cancelled and \
                                                ((self.__processor.test_multithreading()
                                                  and param is None) or (self.__processor.test_multithreading()
                                                                         and test.parallelized_parameters()
                                                                         and param is not None)):

                                                ParallelProcessor.wait_while(lambda: not state.cancelled and
                                                                             self.__processor.test_limit_reached())
                                                Limiter.wait_turn(
                                                    ("test", suite.get_class_object())
                                                    if suite.get_kwargs().get("throttling") is not None else "test",
                                                    Limiter.get_test_throttling(suite), state)
                                                self.__processor.run_test_in_a_thread(
                                                                                      self.__capture_thread_errors(
                                                                                          Runner.__run_test),
                                                                                      suite, test, param,
                                                                                      class_param,
                                                                                      before_class_error,
                                                                                      context)
                                        else:
                                            Runner.__run_test(suite=suite, test=test,
                                                              parameter=param,
                                                              class_parameter=class_param,
                                                              before_class_error=before_class_error,
                                                              cancel=context)
                                    tests.remove(test)

                                else:
                                    tests.remove(test)
                                    test.metrics.update_metrics(status=TestCategory.SKIP, start_time=test_start_time)
                                    Runner.__process_event(event=Event.ON_SKIP, suite=suite, test=test,
                                                           class_param=class_param)
                                    context.console.unit_done(suite, unit_key(test, None, None), TestCategory.SKIP,
                                                              Runner.__label(suite, test))
                        # only this suite's tests - waiting on every suite's tests here held parallel suites back
                        ParallelProcessor.wait_currently_active_tests_to_finish(suite)
                        if state.cancelled:
                            context.console.suite_cleanup(suite, True)
                        Runner.__run_after_class(suite, class_param)
                    suite.metrics.update_suite_metrics(status=SuiteCategory.FAIL
                                                       if suite.has_unsuccessful_tests() else SuiteCategory.SUCCESS,
                                                       start_time=suite_start_time)
            Runner.__process_event(event=Event.ON_CLASS_COMPLETE, suite=suite)
        elif state.cancelled:
            suite.metrics.update_suite_metrics(status=SuiteCategory.CANCEL, start_time=suite_start_time)
            Runner.__process_event(event=Event.ON_CLASS_CANCEL, suite=suite)
        elif exception:
            suite.metrics.update_suite_metrics(status=SuiteCategory.IGNORE, start_time=suite_start_time,
                                               initiation_error=exception)
            Runner.__process_event(event=Event.ON_CLASS_IGNORE, suite=suite)
        else:
            suite.metrics.update_suite_metrics(status=SuiteCategory.SKIP, start_time=suite_start_time)
            Runner.__process_event(event=Event.ON_CLASS_SKIP, suite=suite)

    @staticmethod
    def __overrides(rules, hook):
        """
        :return: BOOLEAN, True if this Rules subclass overrides the hook - the base hooks are no-ops, so for them we
                 skip the call and the per-test copy of the test object it would need
        """
        return getattr(type(rules), hook) is not getattr(Rules, hook)

    @staticmethod
    def __label(suite, test, parameter=None, class_parameter=None):
        label = "{}.{}".format(suite.get_class_name(), test.get_function_name())
        parts = []
        if class_parameter is not None and test.accepts_suite_parameters():
            parts.append("suite: {}".format(class_parameter))
        if parameter is not None:
            parts.append(str(parameter))
        if parts:
            text = ", ".join(parts)
            label += "[{}]".format(text if len(text) <= 40 else text[:39] + "…")
        return label

    @staticmethod
    def __run_test(suite, test, parameter=None, class_parameter=None, before_class_error=None, cancel=False):
        """
        :param cancel: the run's _RunContext, or a BOOLEAN when called outside of run()
        """
        context = cancel if isinstance(cancel, _RunContext) else None
        if context is None:
            return Runner.__run_test_body(suite, test, parameter, class_parameter, before_class_error, bool(cancel))
        key = unit_key(test, parameter, class_parameter)
        label = Runner.__label(suite, test, parameter, class_parameter)
        context.console.unit_started(key, label)
        try:
            Runner.__run_test_body(suite, test, parameter, class_parameter, before_class_error, context.state, context)
        except (TestInterrupted, KeyboardInterrupt):
            raise
        except BaseException as error:  # e.g. the test called sys.exit()
            Runner.__ignore_unit(None, suite, test, parameter, class_parameter, error, traceback.format_exc())
            raise
        finally:
            recorded = class_parameter if test.accepts_suite_parameters() else None
            data = test.metrics.get_metrics().get(str(recorded), {}).get(str(parameter), {})
            context.console.unit_done(suite, key, data.get("status"), label,
                                      runtime=sum(t for t in data.get("performance", []) if t),
                                      runs=len(data.get("statuses", [])),
                                      retries=test.metrics.get_retries(parameter, recorded))

    @staticmethod
    def __run_test_body(suite, test, parameter=None, class_parameter=None, before_class_error=None, cancel=False,
                        context=None):

        def run_before_test():
            try:
                if not test.skip_before_test_rule() and Runner.__overrides(suite.get_rules(), "before_test"):
                    suite.get_rules().before_test(test=TestView(test))
                if not test.skip_before_test():
                    before_test_error = Runner.__process_decorator(decorator_type=DecoratorType.BEFORE_TEST,
                                                                   suite=suite, class_parameter=class_parameter,
                                                                   test=test, parameter=parameter)
                    if before_test_error is not None:  # updating **test** metrics (no decorator passed in)
                        process_failure(before_test_error, pre_processed=True)
                        return False
                return True
            except Exception as before_test_error:
                process_failure(before_test_error, decorator=DecoratorType.BEFORE_TEST)
                process_failure(before_test_error)  # updating **test** metrics (no decorator passed in)
                return False

        def process_failure(error, pre_processed=False, decorator=None):
            _runtime = time.time() - start_time  # start time defined in the outside scope before each decorated func
            if not isinstance(error, TestJunkieExecutionError):
                if pre_processed:
                    trace = str(error)
                else:
                    trace = traceback.format_exc()
                __category, __event = TestCategory.ERROR, Event.ON_ERROR
                if isinstance(error, AssertionError):
                    __category, __event = TestCategory.FAIL, Event.ON_FAILURE
                test.metrics.update_metrics(status=__category,
                                            start_time=test_start_time,
                                            param=parameter,
                                            class_param=class_parameter,
                                            exception=error,
                                            formatted_traceback=trace,
                                            runtime=_runtime,
                                            decorator=decorator)
                if decorator is None:
                    run_errors.append(error)
                    Runner.__process_event(event=__event, suite=suite, test=test, error=error,
                                           class_param=class_parameter, param=parameter, formatted_traceback=trace)
                else:
                    suite.metrics.update_decorator_metrics(decorator, start_time, error, trace)
            else:
                raise error

        def run_after_test(_record_test_failure=True):
            try:
                # Running after test functions
                if not test.skip_after_test():
                    after_test_error = Runner.__process_decorator(decorator_type=DecoratorType.AFTER_TEST,
                                                                  suite=suite, class_parameter=class_parameter,
                                                                  test=test, parameter=parameter)
                    if after_test_error is not None:  # updating **test** metrics (no decorator passed in)
                        process_failure(after_test_error, pre_processed=True)
                        return False
                if not test.skip_after_test_rule() and Runner.__overrides(suite.get_rules(), "after_test"):
                    suite.get_rules().after_test(test=TestView(test))
                return True
            except Exception as after_test_error:
                if _record_test_failure:
                    process_failure(after_test_error, decorator=DecoratorType.AFTER_TEST)
                    process_failure(after_test_error)  # updating **test** metrics (no decorator passed in)
                return False

        if not test.accepts_suite_parameters():
            # for reporting purposes, so reports are properly nested
            class_parameter = None

        cancelled = cancel() if callable(cancel) else cancel
        test_start_time = time.time()
        if before_class_error is not None or cancelled:
            if not test.accepts_suite_parameters():
                if None in test.suite.metrics.get_metrics()[DecoratorType.BEFORE_CLASS]["exceptions"] \
                        and test.get_status(parameter, class_parameter) is not None:
                    return  # fixes ticket: #19
                elif test.get_number_of_actual_retries(parameter, class_parameter) >= test.suite.get_retry_limit():
                    return  # fixes ticket: #27
            _status = TestCategory.IGNORE if not cancelled else TestCategory.CANCEL
            _event = Event.ON_IGNORE if not cancelled else Event.ON_CANCEL
            # a cancel has no @beforeClass error - indexing None here made Runner.cancel() mid-run raise TypeError
            _exception = before_class_error["exception"] if before_class_error else None
            _traceback = before_class_error["traceback"] if before_class_error else None
            test.metrics.update_metrics(status=_status,
                                        start_time=test_start_time,
                                        param=parameter,
                                        class_param=class_parameter,
                                        exception=_exception,
                                        formatted_traceback=_traceback)
            Runner.__process_event(event=_event, error=_exception, suite=suite, test=test,
                                   class_param=class_parameter, param=parameter,
                                   formatted_traceback=_traceback)
            return

        status = test.get_status(parameter, class_parameter)
        if not test.accepts_suite_parameters() and status is not None:
            """
            making sure that we do not run tests with suite parameters if suite parameters are not accepted in the
            test signature. But we still want to run all other parameters and tests without any params.
            Also we want to make sure we honor the suite level retries
            """
            if status != TestCategory.SUCCESS:  # test already ran and was unsuccessful
                # if it did not reach its max retry limit, will rerun it again
                max_retry_allowed = suite.get_retry_limit() * test.get_retry_limit()
                actual_retries = test.get_number_of_actual_retries(parameter, class_parameter)
                if actual_retries >= max_retry_allowed:
                    return
            else:
                return

        Runner.__process_event(event=Event.ON_IN_PROGRESS, suite=suite, test=test,
                               class_param=class_parameter, param=parameter)
        run_errors = []  # the error of each failed run in this loop, as raised
        policy = test.get_retry_policy() if test.retry_override != 1 else None
        try:
            for retry_attempt in range(1, test.get_retry_limit() + 1):
                if retry_attempt > 1 and callable(cancel) and cancel():
                    break  # cancelled: keep the result it has, no more retries
                if retry_attempt > 1 and policy is not None:
                    decision = policy.decide(run_errors)
                    if not decision:
                        break
                    if not Runner.__before_retry(suite, test, parameter, class_parameter, cancel,
                                                 policy.name(), decision.when.label(), decision.delay):
                        break  # cancelled while waiting
                elif retry_attempt > 1 and test.is_qualified_for_retry(parameter, class_param=class_parameter):
                    Runner.__before_retry(suite, test, parameter, class_parameter, cancel, None, None, 0)
                if test.is_qualified_for_retry(parameter, class_param=class_parameter):
                    LogJunkie.debug("\n===============Running test==================\n"
                                    "Test Case: {}\n"
                                    "Test Suite: {}\n"
                                    "Test Parameter: {}\n"
                                    "Class Parameter: {}\n"
                                    "Retry Attempt: {}/{}\n"
                                    "============================================="
                                    .format(test.get_function_name(), suite.get_class_name(), parameter,
                                            class_parameter, retry_attempt, test.get_retry_limit()))
                    pools = Limiter.acquire(Limiter.pools_used(suite, test),
                                            cancel if callable(cancel) else None)
                    if pools is None:  # cancelled while waiting for a pool slot
                        test.metrics.update_metrics(status=TestCategory.CANCEL, start_time=test_start_time,
                                                    param=parameter, class_param=class_parameter)
                        Runner.__process_event(event=Event.ON_CANCEL, suite=suite, test=test,
                                               class_param=class_parameter, param=parameter)
                        return
                    record_test_failure = True
                    capture = Capture()
                    attempt = capturing(context.router if context is not None else None, capture)
                    attempt.__enter__()
                    try:
                        try:
                            start_time = time.time()  # before test start time
                            if run_before_test() is False:  # if before test failed, moving on without running the test
                                continue  # everything recorded at this point in the metrics and flow is solid
                            # Running actual test
                            start_time = time.time()  # test start time
                            test_case_start = start_time
                            in_main = context is not None and threading.current_thread() is threading.main_thread()
                            if in_main:  # lets Ctrl+C interrupt this test, see Runner.__on_interrupt()
                                context.state.main_thread_in_test = True
                            try:
                                Runner.__process_decorator(decorator_type=DecoratorType.TEST_CASE, suite=suite,
                                                           test=test, parameter=parameter,
                                                           class_parameter=class_parameter)
                            finally:
                                if in_main:
                                    context.state.main_thread_in_test = False
                            runtime = time.time() - start_time
                        except (TestInterrupted, KeyboardInterrupt):
                            # Ctrl+C while this test ran on the main thread, or the test raised KeyboardInterrupt
                            if context is not None:
                                context.cancel_by_user()
                            test.metrics.update_metrics(status=TestCategory.CANCEL, start_time=test_start_time,
                                                        param=parameter, class_param=class_parameter,
                                                        runtime=time.time() - start_time)
                            Runner.__process_event(event=Event.ON_CANCEL, suite=suite, test=test,
                                                   class_param=class_parameter, param=parameter)
                            start_time = time.time()
                            run_after_test(False)  # cleanup still runs
                            return
                        except SkipTest:
                            test.metrics.update_metrics(status=TestCategory.SKIP,
                                                        start_time=test_start_time,
                                                        param=parameter,
                                                        class_param=class_parameter)
                            Runner.__process_event(event=Event.ON_SKIP, suite=suite, test=test,
                                                   class_param=class_parameter, param=parameter)
                            return
                        except Exception as test_error:
                            runtime = time.time() - start_time
                            process_failure(test_error)
                            record_test_failure = False  # already recorded the failure just above this
                        start_time = time.time()  # after test start time
                        if run_after_test(record_test_failure) is True:  # if did not fail, test is OK
                            if record_test_failure:  # Test failed and failure was already recorded thus can't pass it
                                test.metrics.update_metrics(status=TestCategory.SUCCESS, start_time=test_case_start, param=parameter,
                                                            class_param=class_parameter, runtime=runtime)
                                Runner.__process_event(event=Event.ON_SUCCESS, suite=suite, test=test,
                                                       class_param=class_parameter, param=parameter)
                                return
                    finally:
                        Limiter.release(pools)
                        attempt.__exit__(None, None, None)
                        if context is not None:
                            test.metrics.record_output(parameter, class_parameter, retry_attempt,
                                                       capture.output(), capture.log)
        finally:
            Runner.__process_event(event=Event.ON_COMPLETE, suite=suite, test=test,
                                   class_param=class_parameter, param=parameter)

    @staticmethod
    def __before_retry(suite, test, parameter, class_parameter, cancel, policy, when, delay):
        """
        Records the retry, tells listeners (on_retry) and waits `delay` seconds without holding any pool slot.
        Returns False if the run was cancelled while waiting.
        """
        runs = test.metrics.get_metrics().get(str(class_parameter), {}).get(str(parameter), {}).get("statuses", [])
        info = {"run": len(runs), "policy": policy, "when": when, "waited": round(delay, 3)}
        test.metrics.record_retry(parameter, class_parameter, info["run"], policy, when, info["waited"])
        Runner.__process_event(event=Event.ON_RETRY, suite=suite, test=test, class_param=class_parameter,
                               param=parameter, extra={"retry": info})
        deadline = time.monotonic() + delay
        while True:
            if callable(cancel) and cancel():
                return False
            left = deadline - time.monotonic()
            if left <= 0:
                return True
            time.sleep(min(left, 0.1))

    @staticmethod
    def __run_before_class(suite, class_parameter=None):
        try:
            suite.get_rules().before_class()
            before_class_error = Runner.__process_decorator(decorator_type=DecoratorType.BEFORE_CLASS,
                                                            suite=suite, class_parameter=class_parameter)
            if before_class_error is not None:
                raise before_class_error
            return
        except Exception as error:
            trace = traceback.format_exc()
            event = Event.ON_BEFORE_CLASS_FAIL if isinstance(error, AssertionError) else Event.ON_BEFORE_CLASS_ERROR
            Runner.__process_event(event=event, suite=suite, error=error,
                                   class_param=class_parameter, formatted_traceback=trace)
            return {"exception": error, "traceback": trace}

    @staticmethod
    def __run_after_class(suite, class_parameter=None):
        try:
            after_class_error = Runner.__process_decorator(decorator_type=DecoratorType.AFTER_CLASS,
                                                           suite=suite, class_parameter=class_parameter)
            if after_class_error is not None:
                raise after_class_error
            suite.get_rules().after_class()
        except Exception as error:
            trace = traceback.format_exc()
            event = Event.ON_AFTER_CLASS_FAIL if isinstance(error, AssertionError) else Event.ON_AFTER_CLASS_ERROR
            Runner.__process_event(event=event, suite=suite, error=error,
                                   class_param=class_parameter, formatted_traceback=trace)
            return {"exception": error, "traceback": trace}

    @staticmethod
    # @synchronized(threading.Lock())
    def __process_decorator(decorator_type, suite, test=None, parameter=None,  class_parameter=None):

        def update_metrics(_decorator_type, error=None, _trace=None):
            suite.metrics.update_decorator_metrics(_decorator_type, start_time, error, _trace)
            if _decorator_type in [DecoratorType.BEFORE_TEST, DecoratorType.AFTER_TEST]:
                test.metrics.update_metrics(status=None, start_time=start_time, param=parameter,
                                            class_param=class_parameter, decorator=_decorator_type,
                                            formatted_traceback=_trace, exception=error)
        start_time = time.time()
        if DecoratorType.TEST_CASE != decorator_type:
            functions_list = suite.get_decorated_definition(decorator_type)
            for func in functions_list:
                try:
                    names = arg_names(func["decorated_function"])
                    kwargs = {}
                    if "suite_parameter" in names:
                        kwargs["suite_parameter"] = class_parameter
                    if "test" in names and test is not None:  # per-test hooks only: a read-only view
                        kwargs["test"] = TestView(test)
                    func["decorated_function"](suite.get_class_instance(), **kwargs)
                except Exception as decorator_error:
                    trace = traceback.format_exc()
                    update_metrics(decorator_type, decorator_error, trace)
                    if DecoratorType.BEFORE_TEST == decorator_type:  # if before test fails, after test wont run
                        if suite.get_decorated_definition(DecoratorType.AFTER_TEST):
                            update_metrics(DecoratorType.AFTER_TEST, None, "N/A")  # but we need to keep list synced
                    return AssertionError(trace) if isinstance(decorator_error, AssertionError) else Exception(trace)
            if functions_list:  # will updated only if we had decorated function(s)
                update_metrics(decorator_type)
        else:
            if test.accepts_test_and_suite_parameters():
                test.get_function_object()(suite.get_class_instance(),
                                           parameter=parameter, suite_parameter=class_parameter)
            elif test.accepts_suite_parameters():
                test.get_function_object()(suite.get_class_instance(), suite_parameter=class_parameter)
            elif test.accepts_test_parameters():
                test.get_function_object()(suite.get_class_instance(), parameter=parameter)
            else:
                test.get_function_object()(suite.get_class_instance())

    @staticmethod
    def __process_event(event, suite, test=None, param=None, class_param=None, error=None, formatted_traceback=None,
                        extra=None):

        name = _EVENT_HANDLERS[event]
        native_function = getattr(_NATIVE_LISTENER, name)
        listener = suite.get_listener()
        # only call the custom listener if it overrides the hook - the base hooks do nothing.
        # This used to build a 21-entry mapping (and 21 Listener objects) for every single event
        custom_function = getattr(listener, name) \
            if getattr(type(listener), name, None) is not getattr(Listener, name) else None

        @synchronized(_EVENT_PROPERTIES_LOCK)
        def __create_properties():
            properties = {"suite_meta": suite.get_meta(copy_of_meta=True),
                          "test_meta": test.get_meta(param, class_param, copy_of_meta=True) if test else None,
                          "jm": {"jso": suite}}
            if test:
                properties["test_meta"].update({"parameter": param})
                properties["jm"].update({"jto": test})
            properties["suite_meta"].update({"parameter": class_param})
            if extra:
                properties.update(extra)
            return properties
        try:

            if error is not None:
                native_function(custom_function=custom_function,
                                properties=__create_properties(),
                                error=error,
                                trace=formatted_traceback)
            else:
                native_function(custom_function=custom_function,
                                properties=__create_properties())
        except Exception as listener_error:
            # recorded instead of raised: raising ended the suite and its remaining tests went unreported.
            # run() raises TestListenerError once every suite is done
            LogJunkie.error("Listener {} raised: {!r}".format(custom_function, listener_error))
            suite.metrics.record_listener_error(name, test, param, class_param, listener_error,
                                                traceback.format_exc())

    @staticmethod
    def __runnable_tags(test, tag_config):
        """
        This function evaluates if test should be executed based on its tags and the tag config
        :param test: TestObject
        :param tag_config: DICT
        :return: BOOLEAN
        """

        def __config_set(prop=None):
            """
            Checks if tag config was defined for any of the following settings:
            - skip_on_match_all
            - skip_on_match_any
            - run_on_match_all
            - run_on_match_any
            :return: BOOLEAN, if any of of the settings are set, tag config is considered set
            """
            props = ["skip_on_match_all", "skip_on_match_any", "run_on_match_all", "run_on_match_any"]
            for setting in props if not prop else [prop]:
                val = tag_config.get(setting, None) is not None
                if val is True:
                    return True
            return False

        def __full_match(prop):
            tags = tag_config.get(prop, [])
            if not tags:
                return False
            for tag in tags:
                if tag not in test_tags:
                    return False
            return True

        def __partial_match(prop):
            tags = tag_config.get(prop, [])
            if not tags:
                return False
            for tag in tags:
                if tag in test_tags:
                    return True

        test_tags = test.get_tags()
        if tag_config is not None:
            try:
                if __config_set():
                    if __full_match("skip_on_match_all") or __partial_match("skip_on_match_any"):
                        return False
                    elif __full_match("run_on_match_all") or __partial_match("run_on_match_any"):
                        return True
                    else:
                        if not __config_set("run_on_match_all") and not __config_set("run_on_match_any"):
                            return True
                        return False

            except Exception:
                raise ConfigError("Error occurred while trying to parse `tag_config`. For help on defining the config, "
                                  "see documentation: {}".format(DocumentationLinks.TAGS))
        return True

    def __positive_skip_condition(self, test):
        """
        This function will evaluate inputs for skip parameter whether its a function or a boolean
        :param test: TestObject object
        :return: BOOLEAN
        """
        can_skip = test.can_skip()

        # Run only tests that were requested: function objects, names, Suite.test names or patterns (login_*)
        if can_skip is False and self.__settings.tests is not None:
            names = (test.get_function_name(), "{}.{}".format(test.suite.get_class_name(), test.get_function_name()))
            requested = test.get_function_object() in self.__settings.tests or \
                any(isinstance(pattern, str) and any(fnmatch.fnmatchcase(name, pattern) for name in names)
                    for pattern in self.__settings.tests)

            can_skip = not requested  # if test was not requested as part of the tests set, we can skip it

        # Out of those tests, run only components that were requested
        if can_skip is False and self.__settings.components is not None:
            can_skip = not test.get_component() in self.__settings.components

        # Out of those tests, run only those that belong to the owners requested
        if can_skip is False and self.__settings.owners is not None:
            can_skip = not test.get_owner() in self.__settings.owners
        return can_skip
