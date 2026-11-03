"""
Stress harness for the end-of-run step (runner.py: console summary, HTML report, XML report).

Executes a generated run through Runner and times the runner's own calls to Console.finish, Reporter (construct +
generate_html_report) and XmlReporter.create_xml_report, each separately. Generated data only.

    python3.13 -m tests.stress.report_stress --tests 1000 --fail-rate 0.3 --reruns 6 --frames 40 [--out DIR]
    python3.13 -m tests.stress.report_stress --case named-300
    python3.13 -m tests.stress.report_stress --matrix --out DIR

Each size runs in subprocesses: a time pass (no tracemalloc) and a memory pass (tracemalloc started and stopped
inside each step, so the peak is what that step allocated). --timeout caps the whole size, both passes together.
"""
import argparse
import json
import os
import platform
import random
import shutil
import subprocess
import sys
import tempfile
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUITE_SIZE = 100
STEPS = ("console", "html_construct", "html_generate", "xml")
MATRIX = [  # criterion 5 of the task that added this harness
    {"tests": 1000, "fail_rate": 0.0, "reruns": 6, "frames": 40},
    {"tests": 1000, "fail_rate": 0.3, "reruns": 6, "frames": 40},
    {"tests": 5000, "fail_rate": 0.1, "reruns": 6, "frames": 40},
    {"tests": 20000, "fail_rate": 0.3, "reruns": 6, "frames": 40},
    {"tests": 300, "fail_rate": 1.0, "reruns": 6, "frames": 40, "name": "named-300"},
]
CASES = {"named-300": MATRIX[-1]}
SMALL = {"tests": 200, "fail_rate": 0.3, "reruns": 6, "frames": 40}  # the size the normal suite gates on
# Seconds the whole end-of-run step (console + HTML construct + HTML generate + XML) may take, by label(size). The one
# place the stress gate's thresholds live (tests/junkie_suites/stress_checks.py)
BUDGETS = {
    # the owner's budget, Tue Nov 3 2026 (TASK-1306)
    "named-300": 30.0,
    "20000-tests-30pct-6-reruns-40-frames": 300.0,
    # no owner number: held to the 20k budget, a bigger run (post-fix total 2.72 s, TASK-1304)
    "5000-tests-10pct-6-reruns-40-frames": 300.0,
    # derived from TASK-1304's post-fix totals: under 2x named-300's 1.67 s and 1k/30%'s 1.27 s (both bigger runs) and
    # ~20x this size's own ~0.14 s, so load or coverage won't trip it; under the pre-fix 6.23 s of the traceback
    # analysis alone at this size, so the quadratic grouping coming back fails it
    "200-tests-30pct-6-reruns-40-frames": 3.0,
}


def end_of_run_seconds(result):
    """
    Seconds of the whole end-of-run step in a run_size result, or None when a step never ran
    """
    if not all(step in result["seconds"] for step in STEPS):
        return None
    return sum(result["seconds"][step] for step in STEPS)


def over_budget(size, result, timeout):
    """
    None when the size finished within BUDGETS[label(size)], else the reason with the harness line
    """
    budget = BUDGETS[label(size)]
    total = end_of_run_seconds(result)
    if result["finished"] and total is not None and total < budget:
        return None
    spent = "did not finish" if total is None else "{:.2f} s".format(total)
    return "end-of-run step {}, budget {:.0f} s: {}".format(spent, budget, format_result(size, result, timeout))


def label(size):
    name = size.get("name") or "{}-tests-{:.0f}pct-{}-reruns-{}-frames".format(
        size["tests"], size["fail_rate"] * 100, size["reruns"], size["frames"])
    return name if size.get("traceback_limit") is None else "{}-{}-chars".format(name, size["traceback_limit"])


# ── The generated run ───────────────────────────────────────────────────────────────────────────────────────────────

_CHAINS = {}


def _chain(frames):
    """
    frames distinct functions, each calling the next, the last raising. Not recursion: Python's traceback folds
    repeated identical frames into "[Previous line repeated N more times]", which would make the text short. The
    source goes into linecache (mtime None, so checkcache keeps it) so each frame shows its line like a real one
    """
    if frames not in _CHAINS:
        import linecache
        filename = "<stress-frames-{}>".format(frames)
        lines = ["def stress_frame_{:03d}(kind, message):\n    stress_frame_{:03d}(kind, message)\n".format(n, n + 1)
                 for n in range(1, frames)]
        lines.append("def stress_frame_{:03d}(kind, message):\n    raise kind(message)\n".format(frames))
        source = "".join(lines)
        namespace = {}
        exec(compile(source, filename, "exec"), namespace)
        linecache.cache[filename] = (len(source), None, source.splitlines(True), filename)
        _CHAINS[frames] = namespace["stress_frame_001"]
    return _CHAINS[frames]


def _failing(index, frames, kind):
    chain = _chain(max(1, frames))

    def body(self):
        chain(kind, "synthetic failure {} at depth {}".format(index, frames))
    return body


def _passing(self):
    pass


def build_suites(tests, fail_rate, reruns, frames, seed=1):
    """
    Suites StressSuite0001... of SUITE_SIZE tests each. A seeded pick of round(tests * fail_rate) tests fails on every
    attempt (worst case), half with AssertionError (failed), half with RuntimeError (error), each from `frames` levels
    deep. retry=reruns + 1: retry counts all runs of a test
    """
    from test_junkie.decorators import Suite, test
    picked = sorted(random.Random(seed).sample(range(tests), int(round(tests * fail_rate))))
    kinds = {index: (AssertionError if n % 2 == 0 else RuntimeError) for n, index in enumerate(picked)}
    suites = []
    for start in range(0, tests, SUITE_SIZE):
        members = {}
        for index in range(start, min(start + SUITE_SIZE, tests)):
            body = _failing(index, frames, kinds[index]) if index in kinds else _passing
            name = "test_%05d" % (index + 1)
            members[name] = test(retry=reruns + 1)(_named(body, name))
        suites.append(Suite()(type("StressSuite%04d" % (start // SUITE_SIZE + 1), (), members)))
    return suites, len(picked)


def _named(body, name):
    def wrapper(self):
        body(self)
    wrapper.__name__ = name
    return wrapper


# ── One pass, in the child process ──────────────────────────────────────────────────────────────────────────────────

def _emit(stream, **record):
    stream.write(json.dumps(record) + "\n")
    stream.flush()


def run_pass(size, out_dir, memory, emit):
    """
    Runs the generated run once with the end-of-run calls wrapped; emit(step=..., seconds=..., peak=...) per step
    """
    import tracemalloc
    from test_junkie.console import Console
    from test_junkie.reporter.html_reporter import Reporter
    from test_junkie.reporter.xml_reporter import XmlReporter
    from test_junkie.runner import Runner

    started = [None]

    def timed(step, func):
        def wrapper(*args, **kwargs):
            if step == "console":
                emit(step="run", seconds=time.perf_counter() - started[0], peak=None)
            if memory:
                tracemalloc.start()
            begin = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                seconds = time.perf_counter() - begin
                peak = None
                if memory:
                    peak = tracemalloc.get_traced_memory()[1]
                    tracemalloc.stop()
                emit(step=step, seconds=seconds, peak=peak)
        return wrapper

    originals = [(Console, "finish", Console.__dict__["finish"]),
                 (Reporter, "__init__", Reporter.__dict__["__init__"]),
                 (Reporter, "generate_html_report", Reporter.__dict__["generate_html_report"]),
                 (XmlReporter, "create_xml_report", XmlReporter.__dict__["create_xml_report"])]
    suites, failing = build_suites(size["tests"], size["fail_rate"], size["reruns"], size["frames"])
    os.makedirs(out_dir, exist_ok=True)
    real_stdout = sys.stdout
    console_file = open(os.path.join(out_dir, "console.txt"), "w", encoding="utf-8")
    Console.finish = timed("console", Console.finish)
    Reporter.__init__ = timed("html_construct", Reporter.__init__)
    Reporter.generate_html_report = timed("html_generate", Reporter.generate_html_report)
    XmlReporter.create_xml_report = staticmethod(timed("xml", XmlReporter.create_xml_report))
    try:
        sys.stdout = console_file  # Console binds sys.stdout when the run starts: the full summary goes to the file
        run_kwargs = {}
        if size.get("traceback_limit") is not None:  # else Test Junkie's default, what users get
            run_kwargs["traceback_limit"] = size["traceback_limit"]
        started[0] = time.perf_counter()
        Runner(suites, html_report=os.path.join(out_dir, "report.html"),
               xml_report=os.path.join(out_dir, "report.xml")).run(**run_kwargs)
    finally:
        sys.stdout = real_stdout
        console_file.close()
        for owner, name, original in originals:
            setattr(owner, name, original)
    return failing


def _child(args):
    size = json.loads(args.child)
    out = sys.stdout
    run_pass(size, args.child_out, args.child_pass == "memory", lambda **record: _emit(out, **record))
    _emit(out, step="done", seconds=None, peak=None)


# ── The parent: one size, both passes, one cap ──────────────────────────────────────────────────────────────────────

def run_size(size, out_dir, passes=("time", "memory"), timeout=1800.0):
    """
    Runs the size's passes in subprocesses, `timeout` seconds for all of them together. Returns
    {"seconds": {step: s}, "peak": {step: bytes}, "finished": bool, "timed_out": the pass stopped at the cap or None,
    "elapsed": s}; a step missing from it never ran. The memory pass is far slower than the time pass (tracemalloc
    traces every allocation: ~40x on the HTML report's difflib calls), so it may be the pass that runs out
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = REPO_ROOT + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    home = None
    if not env.get("TEST_JUNKIE_HOME"):
        home = env["TEST_JUNKIE_HOME"] = tempfile.mkdtemp(prefix="tj_stress_home_")
    result = {"seconds": {}, "peak": {}, "finished": True, "timed_out": None}
    begin = time.monotonic()
    try:
        for kind in passes:
            # the XML report appends to an existing file, so every pass writes fresh files; the first pass's are kept
            pass_dir = out_dir if kind == passes[0] else os.path.join(out_dir, "{}-pass".format(kind))
            if os.path.isdir(pass_dir):
                for name in ("report.html", "report.xml", "console.txt"):
                    if os.path.exists(os.path.join(pass_dir, name)):
                        os.remove(os.path.join(pass_dir, name))
            os.makedirs(pass_dir, exist_ok=True)
            log_path = os.path.join(pass_dir, "{}-pass.jsonl".format(kind))
            with open(log_path, "w", encoding="utf-8") as log:
                child = subprocess.Popen(
                    [sys.executable, "-m", "tests.stress.report_stress", "--child", json.dumps(size),
                     "--child-out", pass_dir, "--child-pass", kind], cwd=REPO_ROOT, env=env, stdout=log)
                try:
                    child.wait(timeout=max(0.0, timeout - (time.monotonic() - begin)))
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
                    result["timed_out"] = kind
            done = False
            with open(log_path, encoding="utf-8") as log:
                for line in log:
                    if not line.startswith("{"):
                        continue
                    record = json.loads(line)
                    if record["step"] == "done":
                        done = True
                    elif kind == "time":
                        result["seconds"][record["step"]] = record["seconds"]
                    elif record["peak"] is not None:
                        result["peak"][record["step"]] = record["peak"]
            os.remove(log_path)
            if pass_dir != out_dir:
                shutil.rmtree(pass_dir, ignore_errors=True)
            if not done:  # timed out, or the child crashed (its traceback is on stderr)
                result["finished"] = False
                if not result.get("timed_out"):
                    result["returncode"] = child.returncode
                break
    finally:
        if home:
            shutil.rmtree(home, ignore_errors=True)
    result["elapsed"] = time.monotonic() - begin
    return result


def format_result(size, result, timeout):
    def step(name, seconds, peak):
        mb = "" if peak is None else " {:.1f} MB".format(peak / 1048576.0)
        return "{} {}{}".format(name, "-" if seconds is None else "{:.2f} s".format(seconds), mb)
    s, p = result["seconds"], result["peak"]
    html_s = s["html_construct"] + s["html_generate"] if "html_construct" in s and "html_generate" in s else None
    html_p = max(p["html_construct"], p["html_generate"]) if "html_construct" in p and "html_generate" in p else None
    head = "{} tests {:.0f}% fail/error {} reruns {} frames".format(
        size["tests"], size["fail_rate"] * 100, size["reruns"], size["frames"])
    if size.get("traceback_limit") is not None:
        head += " traceback limit {}".format(size["traceback_limit"])
    if size.get("name"):
        head = "{} ({})".format(size["name"], head)
    parts = [step("run", s.get("run"), None), step("console.finish", s.get("console"), p.get("console")),
             step("html", html_s, html_p) + " (construct {} + generate {})".format(
                 step("", s.get("html_construct"), p.get("html_construct")).strip(),
                 step("", s.get("html_generate"), p.get("html_generate")).strip()),
             step("xml", s.get("xml"), p.get("xml"))]
    line = "{} | {}".format(head, " | ".join(parts))
    if not result["finished"]:
        stopped = result.get("timed_out")
        if stopped:
            done = s if stopped == "time" else dict(p, run=None)
            where = next((name for name in ("run",) + STEPS if name not in done), "after the last step")
            why = "DID NOT FINISH within {:.0f} min ({} pass stopped in {})".format(timeout / 60.0, stopped, where)
        else:
            why = "child failed, exit code {}".format(result.get("returncode"))
        line += " | {}, stopped after {:.0f} s".format(why, result["elapsed"])
    return line


def _commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                              text=True).stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m tests.stress.report_stress", description=__doc__.split("\n\n")[0])
    parser.add_argument("--tests", type=int, default=1000, help="tests in the run (default 1000)")
    parser.add_argument("--fail-rate", type=float, default=0.3,
                        help="share of tests that fail or error on every attempt, 0-1 (default 0.3)")
    parser.add_argument("--reruns", type=int, default=6, help="reruns of each failing test (default 6)")
    parser.add_argument("--frames", type=int, default=40, help="traceback depth of each failure (default 40)")
    parser.add_argument("--traceback-limit", type=int,
                        help="characters of each traceback the run keeps (default: Test Junkie's, 3000)")
    parser.add_argument("--case", choices=sorted(CASES), help="a named size instead of the values above")
    parser.add_argument("--matrix", action="store_true", help="every size the stress project measures")
    parser.add_argument("--pass", dest="passes", choices=("time", "memory", "both"), default="both")
    parser.add_argument("--timeout", type=float, default=1800.0,
                        help="seconds per size, all passes together; a size over it is stopped (default 1800)")
    parser.add_argument("--out", help="keep each size's report.html, report.xml and console.txt in OUT/<size>/")
    parser.add_argument("--child", help=argparse.SUPPRESS)
    parser.add_argument("--child-out", help=argparse.SUPPRESS)
    parser.add_argument("--child-pass", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.child:
        return _child(args)

    if args.matrix:
        sizes = MATRIX
    elif args.case:
        sizes = [CASES[args.case]]
    else:
        sizes = [{"tests": args.tests, "fail_rate": args.fail_rate, "reruns": args.reruns, "frames": args.frames}]
    if args.traceback_limit is not None:
        sizes = [dict(size, traceback_limit=args.traceback_limit) for size in sizes]
    passes = ("time", "memory") if args.passes == "both" else (args.passes,)
    root = args.out or tempfile.mkdtemp(prefix="tj_stress_")
    print("Python {} on {}, commit {}, passes: {}, cap {:.0f} s per size".format(
        platform.python_version(), platform.platform(), _commit(), "+".join(passes), args.timeout), flush=True)
    try:
        for size in sizes:
            result = run_size(size, os.path.join(root, label(size)), passes, args.timeout)
            print(format_result(size, result, args.timeout), flush=True)
    finally:
        if not args.out:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
