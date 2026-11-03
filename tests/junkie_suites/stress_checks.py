"""
Keeps the end-of-run stress harness (tests/stress/report_stress.py) working, on the pytest and TJ test paths, and
gates the end-of-run step's time on report_stress.BUDGETS: a small size in the normal suite, the large ones on demand
"""
import os
import re
import shutil
import tempfile
import xml.etree.ElementTree as ElementTree

from tests.stress import report_stress


def harness_times_each_end_of_run_step():
    out = tempfile.mkdtemp(prefix="tj_stress_check_")
    try:
        # no truncation, so the whole traceback reaches the report (by default the run keeps 3000 characters of it)
        size = {"tests": 20, "fail_rate": 0.3, "reruns": 1, "frames": 40, "traceback_limit": 100000}
        result = report_stress.run_size(size, out, timeout=300)
        assert result["finished"], result
        assert sorted(result["seconds"]) == sorted(("run",) + report_stress.STEPS), result
        assert sorted(result["peak"]) == sorted(report_stress.STEPS), result
        assert all(peak > 0 for peak in result["peak"].values()), result
        line = report_stress.format_result(size, result, 300)
        for step in ("console.finish", "html", "construct", "generate", "xml"):
            assert re.search(r"\b{} \d+\.\d\d s \d+\.\d MB".format(re.escape(step)), line), line

        # one report per pass would double the XML: it appends to an existing file
        assert sorted(os.listdir(out)) == ["console.txt", "expected.json", "report.html", "report.xml"], os.listdir(out)
        cases = list(ElementTree.parse(os.path.join(out, "report.xml")).getroot().iter("testcase"))
        failed = [case for case in cases if case.find("failure") is not None]
        assert len(cases) == 20 and len(failed) == 6, (len(cases), len(failed))
        reruns = [child.tag for case in failed for child in case if child.tag.startswith("rerun")]
        assert sorted(set(reruns)) == ["rerunError", "rerunFailure"] and len(reruns) == 6, reruns
        trace = failed[0].find("failure").text
        # 40 distinct frames with their source lines; recursion would fold into "[Previous line repeated ...]"
        assert trace.count(", in stress_frame_") == 40 and "repeated" not in trace, trace
        assert "    stress_frame_002(kind, message)" in trace and "synthetic failure" in trace, trace
        with open(os.path.join(out, "report.html"), encoding="utf-8") as report:
            assert "StressSuite0001" in report.read()
        with open(os.path.join(out, "console.txt"), encoding="utf-8") as console:
            assert "StressSuite0001" in console.read()
    finally:
        shutil.rmtree(out, ignore_errors=True)


def harness_stops_a_size_at_its_timeout():
    out = tempfile.mkdtemp(prefix="tj_stress_check_")
    try:
        size = {"tests": 5000, "fail_rate": 0.3, "reruns": 6, "frames": 40}  # well over a minute of run phase
        result = report_stress.run_size(size, out, timeout=1)
        assert not result["finished"] and result["timed_out"] == "time", result
        assert "xml" not in result["seconds"] and result["elapsed"] < 30, result
        line = report_stress.format_result(size, result, 1)
        assert "DID NOT FINISH within 0 min (time pass stopped in run)" in line, line
    finally:
        shutil.rmtree(out, ignore_errors=True)


def _within_budget(size, timeout):
    out = tempfile.mkdtemp(prefix="tj_stress_check_")
    try:
        result = report_stress.run_size(size, out, passes=("time",), timeout=timeout)
        reason = report_stress.over_budget(size, result, timeout)
        assert reason is None, reason
        print("within budget {:.0f} s: {}".format(report_stress.BUDGETS[report_stress.label(size)],
                                                 report_stress.format_result(size, result, timeout)))
    finally:
        shutil.rmtree(out, ignore_errors=True)


def small_run_stays_within_budget():
    _within_budget(report_stress.SMALL, timeout=300)


CHECKS = [harness_times_each_end_of_run_step, harness_stops_a_size_at_its_timeout, small_run_stays_within_budget]

# The large sizes take minutes (mostly the 20k run phase): on demand only, with TJ_STRESS_LARGE=1 set before the run
# starts. Without it both test paths report them skipped
LARGE_ENABLED = os.environ.get("TJ_STRESS_LARGE") == "1"


def _large(size):
    def check():
        _within_budget(size, timeout=1800)
    check.__name__ = "large_run_stays_within_budget_{}".format(report_stress.label(size).replace("-", "_"))
    return check


LARGE_CHECKS = [_large(size) for size in report_stress.MATRIX if report_stress.label(size) in report_stress.BUDGETS]
