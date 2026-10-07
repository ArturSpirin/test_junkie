[![Tests](https://github.com/ArturSpirin/test_junkie/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/ArturSpirin/test_junkie/actions/workflows/tests.yml)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/ArturSpirin/test_junkie/graphs/commit-activity)
[![Known Vulnerabilities](https://snyk.io/test/github/ArturSpirin/test_junkie/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/ArturSpirin/test_junkie?targetFile=requirements.txt)
[![PyPI version shields.io](https://img.shields.io/pypi/v/test_junkie.svg)](https://pypi.python.org/pypi/test_junkie/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/test_junkie.svg)](https://pypi.python.org/pypi/test_junkie/)
[![codecov](https://codecov.io/gh/ArturSpirin/test_junkie/branch/master/graph/badge.svg)](https://codecov.io/gh/ArturSpirin/test_junkie)
[![Downloads](https://pepy.tech/badge/test-junkie)](https://pepy.tech/project/test-junkie)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENCE)

<p align="center">
  <a href="https://www.test-junkie.com/">
    <img src="assets/logo.svg" alt="Test Junkie" width="360">
  </a>
  <br><br>
  <strong>The Python test runner built for precision.</strong><br>
  ▸ Zero plugins. Full arsenal.
</p>

# Test Junkie [![Share on X](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Just+found+Test+Junkie+%E2%80%94+a+Python+test+runner+with+built-in+parallelism%2C+exception-aware+retries%2C+multi-layer+parametrization%2C+and+zero+plugins+required.+This+is+how+Python+testing+should+feel.+%F0%9F%8E%AF&url=https%3A%2F%2Ftest-junkie.com&hashtags=python,testing,automation&original_referer=https%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton)

Test Junkie is a Python test runner and test framework with built-in parallel test execution, exception-aware
retries, multi-layer parametrization, event listeners and HTML/XML reports — everything in one package, no plugins.
Use it from Python with `Runner` or from the terminal with the `tj` command.

## Key Features

> Not a wrapper around `unittest`. Every capability below ships with the library — no plugins to install, no config files to write, no external orchestrators.

- Decorator-based: `@Suite` and `@test` on plain Python classes — no base class to extend, no config file to maintain
- Lifecycle hooks: `@beforeClass`, `@afterClass`, `@beforeTest`, `@afterTest` on the class, plus `@beforeGroup` / `@afterGroup` (via `@GroupRules`) that run once around a named set of suites
- Built-in parallel execution: separate thread limits for suites (`-S` / `suite_multithreading_limit`) and tests (`-T` / `test_multithreading_limit`); `parallelized=False` keeps a suite or test out of the parallel pool, and `pr=[...]` stops specific suites or tests from ever overlapping
- Retries: `retry=N` on a suite or a test — only the failing parameter variants re-run; `retry_on=[ConnectionError]` retries just infrastructure noise, `no_retry_on=[AssertionError]` makes real bugs surface immediately
- Multi-layer parametrization: `@Suite(parameters=[...])` × `@test(parameters=[...])` = every combination, each variant tracked and retried on its own; parameters can be a function that builds the list at run time
- `Rules` for shared setup/teardown — define `before_class` / `before_test` / … once, attach with `@Suite(rules=...)` to as many suites as you like
- First-class `owner`, `feature`, `component`, `tags` and `priority` — filter with `tj run --owners`, `--features`, `--components`, `--tags-any` / `--tags-all` (tags), or `owners=` / `features=` / `components=` / `tag_config=` in `Runner.run()`
- Execution order per suite: `@Suite(order=TestOrder.RANDOM)` (or `ALPHABETICAL`, `PRIORITY_ASC`, `PRIORITY_DESC`) — e.g. shuffle one suite to surface order dependencies
- Skipping: `skip=True` or a function deciding at run time on any suite or test, and `shortcuts.skip("reason")` from inside a running test
- Live event listeners: subclass `Listener`, override any of its 21 events (`on_failure`, `on_success`, `on_class_skip`, …) and attach it with `@Suite(listener=...)`
- Results as objects: `runner.get_executed_suites()` returns typed suite/test objects with status, timing, retries, exceptions and metadata; `Meta.update(...)` adds to a test's metadata while it runs
- Reports: HTML (with CPU and memory graphs when `monitor_resources=True`) and XML, written to the paths you pass as `html_report=` / `xml_report=`; the JSON-ready report data is also returned by `runner.run()`
- CLI: `tj run`, `tj audit`, `tj config` — run and inspect suites without writing a runner script; `tj run` exits non-zero on failures, errors or when nothing ran, ready for CI

And [more →](https://www.test-junkie.com/documentation/)

## Installation

```
pip install test-junkie
```

## Quick example

```python
from test_junkie.decorators import Suite, test, beforeClass
from test_junkie.runner import Runner


@Suite(feature="Login", owner="qa-team")
class LoginSuite:

    @beforeClass()
    def open_session(self):
        self.session = {"user": "demo"}

    @test(component="auth", tags=["smoke"], retry=2)
    def valid_login(self):
        assert self.session["user"] == "demo"

    @test(component="auth", parameters=["", "wrong-password"])
    def invalid_login(self, parameter):
        assert parameter != "correct-password"


if __name__ == "__main__":
    Runner([LoginSuite], html_report="report.html").run(test_multithreading_limit=4)
```

Or from the terminal: `tj run -s path/to/tests -T 4 --html-report report.html`

> **Python 2.7:** the last release with Python 2.7 support is [`0.8a.8`](https://pypi.org/project/test-junkie/0.8a.8/). All versions from `0.9a0` onwards require Python 3.

## Performance

Key takeaways (median of 30 runs; every run verified to have passed all of its tests):

- **1.4× faster than pytest, sequentially** (1.97 s vs 2.74 s, 1,000 tests). Fastest of the four runners: 1.7× faster than Robot Framework (3.39 s) and just ahead of plain unittest (2.03 s).
- **6.7× faster than pytest-xdist in parallel** (0.31 s vs 2.06 s, 1,000 tests, 10 workers). Tests run on threads inside one process, so there's no worker start-up cost, and no plugin to install.
- **Parallelism that scales:** going from 1 to 10 threads makes a 1,000-test run 6.2× faster. pytest-xdist peaks at ×1.7; pabot is slower than sequential Robot Framework at every setting.
- **6.2× smaller than pytest with the plugins for the same features** (3,345 KB vs 20,680 KB installed, every dependency included). Parallel execution, parametrization, retries, listeners, ordering and HTML/XML/JSON reports ship in one package; pytest needs 10 plugins for them, which pull in 18 more packages. Robot Framework with plugins is 8,005 KB (2.4×) and covers 13 of the 19 features. Details: [install size](https://www.test-junkie.com/install-size/).
- **~1 ms framework overhead per test** at 1,000 tests (+972 ms total), vs +1,028 ms for unittest, +1,741 ms for pytest and +2,395 ms for Robot Framework.
- **95 ms start-up for a 1-test run**, on par with unittest (92 ms) and about a third of pytest (296 ms) or Robot Framework (308 ms).

Measured with test_junkie 0.9a5, pytest 9.1.1, Robot Framework 7.5 on Python 3.12.5 (Windows 11, Intel Core i9-10980HK).
Full results tables, parametrized and parallel runs, per-phase timings and the exact commands are in the
[full benchmark →](https://www.test-junkie.com/performance/)

## Getting Started

<p align="center">
  <a href="https://www.test-junkie.com/get-started/"><img src="https://img.shields.io/badge/Getting%20Started%20Guide-f37814?style=for-the-badge" alt="Getting Started Guide"></a>
  &nbsp;
  <a href="https://www.test-junkie.com/documentation/"><img src="https://img.shields.io/badge/Full%20Documentation-3a3f4b?style=for-the-badge" alt="Full Documentation"></a>
</p>

---

<p align="center">
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/Changelog-recent%20changes-3a3f4b?style=flat-square" alt="Changelog"></a>
  &nbsp;&nbsp;
  <a href="https://github.com/ArturSpirin/test_junkie/issues/new?template=bug_report.md"><img src="https://img.shields.io/badge/Bug%20Report-open%20an%20issue-b92c2c?style=flat-square" alt="Report a Bug"></a>
</p>
