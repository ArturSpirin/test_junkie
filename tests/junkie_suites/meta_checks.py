"""
Meta.update redesign (0.9a8): run context per thread, Meta.update(**values) / Meta.get / Meta.bind, strict old-style
calls, Meta.suite.update in class hooks, per-attempt records, listener properties and reports. Shared by both test
paths: tests/pytest/predeploy_tests/rules/test_meta.py and tests/test_junkie/predeploy_tests/test_meta.py
"""
import json
import os
import tempfile
import threading
import warnings

from test_junkie import meta as meta_module
from test_junkie.builder import Builder
from test_junkie.decorators import Suite, test, beforeTest, afterTest, beforeClass
from test_junkie.errors import TestJunkieUsageError
from test_junkie.listener import Listener
from test_junkie.meta import Meta, meta, TestJunkieMetaWarning
from test_junkie.runner import Runner

EVENTS = []
ERRORS = []
COUNTS = {}


class Capture(Listener):

    def __record(self, event, properties):
        EVENTS.append({"event": event, "test": properties["jm"].get("jto"),
                       "test_meta": properties["test_meta"], "suite_meta": properties["suite_meta"],
                       "meta_attempts": properties["meta_attempts"]})

    def on_complete(self, properties):
        self.__record("complete", properties)

    def on_failure(self, properties, exception, trace):
        self.__record("failure", properties)


def _helper():
    Meta.update(helper=True)  # no self, no parameters: lands on whatever test is running


@Suite(parameters=["admin", "viewer"], listener=Capture)
class NewStyleSuite:

    @beforeTest()
    def before(self):
        Meta.update(from_before="yes")

    @afterTest()
    def after(self):
        Meta.update(from_after="yes")

    @test(parameters=[1, 2], meta=meta(name="Orders"))
    def orders(self, parameter, suite_parameter):
        Meta.update(account=suite_parameter, page=parameter)
        _helper()
        assert Meta.get("account") == suite_parameter and Meta.get("name") == "Orders"
        assert Meta.get()["page"] == parameter


@Suite()
class ThreadSuite:

    @test()
    def threaded(self):
        def work():
            Meta.update(from_thread=True)
        worker = threading.Thread(target=Meta.bind(work))
        worker.start()
        worker.join()

        def unbound():
            try:
                Meta.update(lost=True)
            except TestJunkieUsageError as error:
                ERRORS.append(error)
        worker = threading.Thread(target=unbound)
        worker.start()
        worker.join()

    @test()
    def stack_found(self):
        # QATitan's ScaleRules run the test body in worker threads with no run context: the old call still finds
        # the test through the call stack (this function shares the test's name)
        suite = self

        def stack_found():
            Meta.update(suite, from_worker=True)
        worker = threading.Thread(target=stack_found)
        worker.start()
        worker.join()


@Suite(parameters=["admin"])
class OldStyleSuite:

    @test(parameters=[1])
    def strict(self, parameter, suite_parameter):
        Meta.update(self, parameter=parameter, suite_parameter=suite_parameter, ok="running slot")
        Meta.update(self, parameter=parameter, wrong="no suite parameter")  # today's slot: suite parameter None

    @test()
    def reads(self):
        Meta.update(self, expected="5 rows")
        assert Meta.get_meta("expected") == "5 rows"
        assert Meta.get_meta(self)["expected"] == "5 rows"


@Suite()
class KeywordSuiteSuite:

    @test()
    def keyword(self):
        Meta.update(suite=self, expected="x")  # 0.9a7's keyword form of the old call
        assert Meta.get_meta(suite=self)["expected"] == "x"

    @test()
    def plain_key(self):
        Meta.update(suite="checkout")  # a plain "suite" value is just a key


@Suite(parameters=["eu", "us"], listener=Capture, meta=meta(team="core"))
class ClassHookSuite:

    @beforeClass()
    def setup(self, suite_parameter):
        Meta.suite.update(region=suite_parameter)
        try:
            Meta.update(nope=True)
        except TestJunkieUsageError as error:
            ERRORS.append(error)

    @test()
    def uses(self, suite_parameter):
        assert Meta.suite.get("region") == suite_parameter


def _mark(name):
    COUNTS[name] = COUNTS.get(name, 0) + 1
    return COUNTS[name]


class Unprintable(object):
    def __str__(self):
        return "<unprintable widget>"


@Suite(listener=Capture)
class AttemptsSuite:

    @test(retry=2)
    def second_time(self):
        run = _mark("second_time")
        Meta.update(run=0)
        Meta.update(run=run, **({"first": True} if run == 1 else {"second": True}))  # latest value per key kept
        if run == 1:
            assert False, "first run fails"

    @test()
    def odd_values(self):
        Meta.update(raw=b"caf\xc3\xa9 \xff", widget=Unprintable(), long="x" * 3000, nested={"ids": (1, 2)})


@Suite(listener=Capture)
class VisibilitySuite:

    @afterTest()
    def after(self):
        Meta.update(after="set")

    @test()
    def fails(self):
        Meta.update(body="set")
        assert False, "on purpose"


def _run(suites, **kwargs):
    EVENTS.clear()
    ERRORS.clear()
    COUNTS.clear()
    meta_module._WARNED.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        Runner(suites).run(quiet=True, **kwargs)
    return [str(w.message) for w in caught if issubclass(w.category, TestJunkieMetaWarning)]


def _test(suite_class, name):
    for test_object in Builder.get_execution_roster().get(suite_class).get_test_objects():
        if test_object.get_function_name() == name:
            return test_object
    raise AssertionError(name)


def _events(event, name):
    return [e for e in EVENTS if e["event"] == event and e["test"] is not None
            and e["test"].get_function_name() == name]


def update_reaches_the_running_test_from_test_helpers_and_hooks():
    _run([NewStyleSuite])
    orders = _test(NewStyleSuite, "orders")
    for account in ("admin", "viewer"):
        for page in (1, 2):
            values = orders.get_meta(page, account)
            assert values == {"name": "Orders", "account": account, "page": page, "helper": True,
                              "from_before": "yes", "from_after": "yes"}, values
            assert orders.get_status(page, account) == "success"


def declared_meta_is_left_alone():
    _run([NewStyleSuite])
    assert _test(NewStyleSuite, "orders").get_kwargs()["meta"] == {"name": "Orders"}


def bind_carries_the_test_into_threads():
    _run([ThreadSuite])
    assert _test(ThreadSuite, "threaded").get_meta().get("from_thread") is True
    assert len(ERRORS) == 1 and "Meta.bind" in str(ERRORS[0])  # a thread without bind gets told how to fix it
    assert _test(ThreadSuite, "stack_found").get_meta().get("from_worker") is True


def old_style_writes_exactly_the_slot_it_names():
    caught = _run([OldStyleSuite])
    strict = _test(OldStyleSuite, "strict")
    assert strict.get_meta(1, "admin").get("ok") == "running slot" and "wrong" not in strict.get_meta(1, "admin")
    assert strict.get_meta(1, None).get("wrong") == "no suite parameter"  # not filled in from the running test
    mismatch = [m for m in caught if "but the test runs as" in m]
    assert len(mismatch) == 1 and "suite parameter None" in mismatch[0], caught
    assert _test(OldStyleSuite, "reads").get_status(None, None) == "success"


def _call_outside_twice():
    for _ in range(2):
        Meta.update(OldStyleSuite(), dropped=True)


def outside_a_test_old_style_warns_once_new_style_raises():
    _run([OldStyleSuite])
    # on the Test Junkie path this check itself runs inside a test: step outside its run context
    previous = meta_module.enter_context(None)
    try:
        _outside_checks()
    finally:
        meta_module.leave_context(previous)


def _outside_checks():
    meta_module._WARNED.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _call_outside_twice()
    dropped = [str(w.message) for w in caught if issubclass(w.category, TestJunkieMetaWarning)]
    assert len(dropped) == 1 and "dropped" in dropped[0], dropped  # one warning per call site, run carries on
    for call in (lambda: Meta.update(x=1), lambda: Meta.get("x"), lambda: Meta.bind(print), Meta.suite.get):
        try:
            call()
        except TestJunkieUsageError:
            continue
        raise AssertionError("no TestJunkieUsageError")
    assert Meta.get_meta("expected") is None  # a key lookup never raises


def class_hooks_write_suite_meta():
    _run([ClassHookSuite])
    completes = _events("complete", "uses")
    regions = sorted((e["suite_meta"]["region"], e["suite_meta"]["parameter"], e["suite_meta"]["team"])
                     for e in completes)
    assert regions == [("eu", "eu", "core"), ("us", "us", "core")], regions
    assert len(ERRORS) == 2 and all("Meta.suite.update" in str(e) for e in ERRORS)  # plain update points there
    assert _test(ClassHookSuite, "uses").get_status(None, "eu") == "success"
    assert Builder.get_execution_roster().get(ClassHookSuite).get_meta() == {"team": "core"}  # declared untouched


def retries_carry_forward_and_keep_each_attempt():
    _run([AttemptsSuite])
    second_time = _test(AttemptsSuite, "second_time")
    assert second_time.get_meta() == {"run": 2, "first": True, "second": True}
    attempts = [{"attempt": 1, "meta_set": {"run": 1, "first": True}},
                {"attempt": 2, "meta_set": {"run": 2, "second": True}}]
    assert second_time.get_meta_attempts() == attempts
    complete = _events("complete", "second_time")[-1]
    assert complete["meta_attempts"] == attempts
    assert complete["test_meta"] == {"run": 2, "first": True, "second": True, "parameter": None}


def on_failure_sees_body_values_not_after_test():
    _run([VisibilitySuite])
    failure = _events("failure", "fails")[0]["test_meta"]
    complete = _events("complete", "fails")[0]["test_meta"]
    assert failure.get("body") == "set" and "after" not in failure, failure
    assert complete.get("body") == "set" and complete.get("after") == "set", complete


def json_report_has_meta_and_what_each_run_set():
    path = os.path.join(tempfile.mkdtemp(), "report.json")
    _run([AttemptsSuite], json_report=path)
    with open(path, encoding="utf-8") as doc:
        tests = {t["name"]: t for t in json.load(doc)["suites"][0]["tests"]}
    second = tests["second_time"]
    assert second["meta"] == {"run": 2, "first": True, "second": True}
    assert [r["meta_set"] for r in second["runs"]] == [{"run": 1, "first": True}, {"run": 2, "second": True}]
    odd = tests["odd_values"]["meta"]
    assert odd["raw"] == "café �" and odd["widget"] == "<unprintable widget>" and odd["nested"] == {"ids": [1, 2]}
    assert odd["long"].startswith("x" * 2000) and odd["long"].endswith("[cut 1000 characters]")


def xml_report_has_properties_parameters_and_time():
    from xml.etree.ElementTree import parse
    path = os.path.join(tempfile.mkdtemp(), "report.xml")
    _run([NewStyleSuite], xml_report=path)
    cases = {case.get("name"): case for case in parse(path).getroot().iter("testcase")}
    assert sorted(cases) == ["orders[suite: admin, 1]", "orders[suite: admin, 2]",
                             "orders[suite: viewer, 1]", "orders[suite: viewer, 2]"], sorted(cases)
    case = cases["orders[suite: viewer, 2]"]
    properties = {p.get("name"): p.get("value") for p in case.find("properties")}
    assert properties["account"] == "viewer" and properties["page"] == "2" and properties["name"] == "Orders"
    assert case.get("classname") == "NewStyleSuite" and float(case.get("time")) >= 0


def html_report_shows_meta_per_attempt():
    folder = tempfile.mkdtemp()
    _run([AttemptsSuite], html_report=os.path.join(folder, "report.html"))
    with open(os.path.join(folder, "report.html"), encoding="utf-8") as doc:
        page = doc.read()
    assert "function metaBlock" in page  # the panel renderer
    compact = page.replace(" ", "")
    assert '"meta":{"run":2,"first":true,"second":true}' in compact, "variant meta missing"
    assert '"meta":{"run":1,"first":true}' in compact and '"meta":{"run":2,"second":true}' in compact


def rerun_ignores_the_new_fields():
    path = os.path.join(tempfile.mkdtemp(), "report.json")
    _run([VisibilitySuite, AttemptsSuite], json_report=path)
    _run([VisibilitySuite, AttemptsSuite], rerun=path)
    assert _test(VisibilitySuite, "fails").get_status(None, None) == "fail"  # the failed test ran again from the report


PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
       b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")
BIG = b"z" * (meta_module.ATTACH_EMBED_LIMIT + 1)
SOURCE = {}


@Suite(listener=Capture)
class EvidenceSuite:

    @test(retry=2, meta=meta(steps=["declared step"]))
    def evidence(self):
        run = _mark("evidence")
        Meta.append("steps", "run {}".format(run))
        Meta.link("Ticket", "https://example.com/T-{}".format(run))
        Meta.link("Runbook", "https://example.com/runbook")  # the same link every run: listed once
        Meta.attach("page.png", PNG)
        if run == 1:
            source = os.path.join(tempfile.mkdtemp(), "server.log")
            with open(source, "wb") as log:
                log.write(BIG)
            SOURCE["path"] = source
            Meta.attach("server.log", source)
            with open(source, "wb") as log:
                log.write(b"changed after attach")  # the copy taken at attach time is what's kept
            assert False, "first run fails"

    @test()
    def misuse(self):
        Meta.update(note="plain text")
        for call in (lambda: Meta.append("note", 1), lambda: Meta.attach("x", 12345),
                     lambda: Meta.attach("x", os.path.join(tempfile.gettempdir(), "no_such_file_tj.bin"))):
            try:
                call()
            except TestJunkieUsageError as error:
                ERRORS.append(error)


def append_link_and_attach_build_lists_per_attempt():
    _run([EvidenceSuite])
    evidence = _test(EvidenceSuite, "evidence")
    values = evidence.get_meta()
    assert values["steps"] == ["declared step", "run 1", "run 2"], values["steps"]
    assert values["links"] == [{"label": "Ticket", "url": "https://example.com/T-1"},
                               {"label": "Runbook", "url": "https://example.com/runbook"},
                               {"label": "Ticket", "url": "https://example.com/T-2"}], values["links"]
    attachments = values["attachments"]
    assert [a["name"] for a in attachments] == ["page.png", "server.log", "page.png"]
    png, log = attachments[0], attachments[1]
    assert png["mime"] == "image/png" and png["size"] == len(PNG) and png["source"] is None
    with open(png["path"], "rb") as saved:
        assert saved.read() == PNG
    assert log["source"] == SOURCE["path"] and log["size"] == len(BIG) and log["path"] != log["source"]
    assert evidence.get_kwargs()["meta"] == {"steps": ["declared step"]}  # declared list not mutated
    by_attempt = {a["attempt"]: a["meta_set"] for a in evidence.get_meta_attempts()}
    assert by_attempt[1]["steps"] == ["run 1"] and by_attempt[2]["steps"] == ["run 2"]
    assert by_attempt[2]["links"][-1]["label"] == "Runbook"  # each attempt still records what it added
    assert [a["name"] for a in by_attempt[1]["attachments"]] == ["page.png", "server.log"]
    assert _events("complete", "evidence")[-1]["test_meta"]["links"][2]["url"] == "https://example.com/T-2"


def append_and_attach_reject_bad_input():
    _run([EvidenceSuite])
    assert len(ERRORS) == 3, ERRORS
    assert "already holds a str" in str(ERRORS[0]) and "bytes or a file path" in str(ERRORS[1])
    assert "is not a file" in str(ERRORS[2])
    assert _test(EvidenceSuite, "misuse").get_meta()["note"] == "plain text"


def html_report_embeds_small_attachments_and_links_big_ones():
    folder = tempfile.mkdtemp()
    _run([EvidenceSuite], html_report=os.path.join(folder, "run.html"))
    with open(os.path.join(folder, "run.html"), encoding="utf-8") as doc:
        page = doc.read()
    assert "data:image/png;base64," in page and "function metaValue" in page
    log = _test(EvidenceSuite, "evidence").get_meta()["attachments"][1]
    copied = os.path.join(folder, "run_files", os.path.basename(log["path"]))
    assert os.path.getsize(copied) == len(BIG)
    assert "run_files/" + os.path.basename(log["path"]) in page


def keyword_suite_is_the_old_call_not_a_meta_key():
    # Meta.update(suite=self, ...) used to store the suite instance itself under "suite"
    _run([KeywordSuiteSuite])
    keyword = _test(KeywordSuiteSuite, "keyword")
    assert keyword.get_status(None, None) == "success", keyword.get_status(None, None)
    assert keyword.get_meta() == {"expected": "x"}, keyword.get_meta()
    assert _test(KeywordSuiteSuite, "plain_key").get_meta() == {"suite": "checkout"}


CHECKS = [update_reaches_the_running_test_from_test_helpers_and_hooks, declared_meta_is_left_alone,
          bind_carries_the_test_into_threads, old_style_writes_exactly_the_slot_it_names,
          outside_a_test_old_style_warns_once_new_style_raises, class_hooks_write_suite_meta,
          retries_carry_forward_and_keep_each_attempt, on_failure_sees_body_values_not_after_test,
          json_report_has_meta_and_what_each_run_set, xml_report_has_properties_parameters_and_time,
          html_report_shows_meta_per_attempt, rerun_ignores_the_new_fields,
          append_link_and_attach_build_lists_per_attempt, append_and_attach_reject_bad_input,
          html_report_embeds_small_attachments_and_links_big_ones, keyword_suite_is_the_old_call_not_a_meta_key]
