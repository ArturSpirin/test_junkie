"""
Checks for test_junkie.shortcuts.capture_output() (G6). Run by both test paths:
tests/pytest/predeploy_tests/test_capture_output.py and tests/test_junkie/predeploy_tests/test_capture_output.py.
On the pytest path a check runs outside any Test Junkie run, on the TJ path inside the outer run's test: both routes
get covered. The outside-a-run stream swapping is checked in a separate process, where nothing else owns sys.stdout
"""
import contextlib
import io
import os
import subprocess
import sys
import textwrap
import threading

from test_junkie.decorators import Suite, test
from test_junkie.runner import Runner
from test_junkie.shortcuts import capture_output

ROOT = os.path.abspath(__file__).split(os.sep + "tests" + os.sep)[0]
SEEN = {}


@Suite()
class CaptureReportSuite:

    @test()
    def prints_inside_and_outside(self):
        print("OUT-OF-BLOCK")
        with capture_output() as output:
            print("IN-BLOCK")
            print("IN-BLOCK-ERR", file=sys.stderr)
        SEEN["report"] = (output.stdout, output.stderr)
        assert False, "fails so the report shows its output"


@Suite()
class CaptureParallelSuite:

    BARRIER = threading.Barrier(2, timeout=10)

    @test(parameters=["MARK-A", "MARK-B"], parallelized_parameters=True)
    def prints_its_own_marker(self, parameter):
        with capture_output() as output:
            CaptureParallelSuite.BARRIER.wait()  # both tests are inside their blocks at once
            for _ in range(200):
                print(parameter)
            CaptureParallelSuite.BARRIER.wait()
        SEEN[parameter] = output.stdout


@Suite()
class CaptureInnerSuite:

    @test()
    def passes(self):
        print("INNER-PASS")

    @test()
    def fails(self):
        print("INNER-FAIL")
        assert False


def _run(suites, **kwargs):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        aggregator = Runner(suites).run(**kwargs)
    return aggregator, out.getvalue()


def stdout_and_stderr_are_split_and_returned():
    with capture_output() as output:
        print("hello")
        print("oops", file=sys.stderr)
        sys.stdout.write("more")
        assert output.stdout == "hello\nmore", output.stdout  # readable inside the block
    print("after the block")
    assert output.stdout == "hello\nmore", output.stdout
    assert output.stderr == "oops\n", output.stderr


def captured_text_is_not_repeated_in_the_report():
    SEEN.clear()
    _, out = _run([CaptureReportSuite])
    assert SEEN["report"] == ("IN-BLOCK\n", "IN-BLOCK-ERR\n"), SEEN
    assert "OUT-OF-BLOCK" in out, out  # printed outside the block, so the failing test's output still shows it
    assert "IN-BLOCK" not in out, out


def parallel_tests_each_capture_only_their_own_output():
    SEEN.clear()
    _, out = _run([CaptureParallelSuite], test_multithreading_limit=2)
    assert SEEN.get("MARK-A") == "MARK-A\n" * 200, (SEEN, out)
    assert SEEN.get("MARK-B") == "MARK-B\n" * 200, (SEEN, out)
    assert "MARK-" not in out, out


def nested_blocks_innermost_gets_the_text():
    with capture_output() as outer:
        print("outer-1")
        with capture_output() as inner:
            print("inner")
        print("outer-2")
    assert inner.stdout == "inner\n", inner.stdout
    assert outer.stdout == "outer-1\nouter-2\n", outer.stdout


def run_started_inside_a_block_keeps_its_tests_output():
    with capture_output() as output:
        Runner([CaptureInnerSuite]).run()
    # the inner run's report lands in the block; its tests' prints went into the inner run's own capture, so only
    # the failing test's output is in it, once, under the report
    assert "INNER-FAIL" in output.stdout and output.stdout.count("INNER-FAIL") == 1, output.stdout
    assert "INNER-PASS" not in output.stdout, output.stdout


def no_capture_run_still_captures_the_block():
    SEEN.clear()
    _, out = _run([CaptureReportSuite], capture=False)
    assert SEEN["report"] == ("IN-BLOCK\n", "IN-BLOCK-ERR\n"), SEEN
    assert "OUT-OF-BLOCK" in out and "IN-BLOCK" not in out, out


_OUTSIDE_A_RUN = textwrap.dedent("""
    import sys, threading
    sys.path.insert(0, {root!r})
    from test_junkie.console import _Stream
    from test_junkie.shortcuts import capture_output

    out, err = sys.stdout, sys.stderr
    with capture_output() as output:
        print("plain")
        assert sys.stdout is not out
    assert sys.stdout is out and sys.stderr is err, "streams not put back"
    assert output.stdout == "plain\\n", output.stdout

    # two threads, entering and leaving in crossed order: A in, B in, A out, B out
    steps = [threading.Event() for _ in range(4)]
    seen = {{}}

    def a():
        with capture_output() as mine:
            steps[0].set(); steps[1].wait(5)
            print("from-a")
        seen["a"] = mine.stdout
        steps[2].set()

    def b():
        steps[0].wait(5)
        with capture_output() as mine:
            steps[1].set(); steps[2].wait(5)
            print("from-b")
        seen["b"] = mine.stdout

    threads = [threading.Thread(target=a), threading.Thread(target=b)]
    [t.start() for t in threads]
    [t.join(10) for t in threads]
    assert seen == {{"a": "from-a\\n", "b": "from-b\\n"}}, seen
    assert sys.stdout is out and sys.stderr is err, "streams not put back after crossed blocks"

    # a run that ended while something else replaced its stream leaves an inactive _Stream in the chain
    class Ended(object):
        active = False
        capture_enabled = True
    left = _Stream(Ended(), out, "out")
    sys.stdout = left
    with capture_output() as output:
        print("via-chain")
        left.write("direct")  # written straight to the inactive _Stream
    assert sys.stdout is left, "inactive _Stream not put back"
    sys.stdout = out
    assert output.stdout == "via-chain\\ndirect", output.stdout
    print("OUTSIDE-OK")
""")


def outside_a_run_puts_the_streams_back():
    script = _OUTSIDE_A_RUN.format(root=ROOT)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    process = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, encoding="utf-8",
                             env=env, timeout=60)
    out = process.stdout + process.stderr
    assert process.returncode == 0 and out.strip() == "OUTSIDE-OK", out


CHECKS = [stdout_and_stderr_are_split_and_returned, captured_text_is_not_repeated_in_the_report,
          parallel_tests_each_capture_only_their_own_output, nested_blocks_innermost_gets_the_text,
          run_started_inside_a_block_keeps_its_tests_output, no_capture_run_still_captures_the_block,
          outside_a_run_puts_the_streams_back]
