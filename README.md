[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/ArturSpirin/test_junkie/graphs/commit-activity)
[![Known Vulnerabilities](https://snyk.io/test/github/ArturSpirin/test_junkie/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/ArturSpirin/test_junkie?targetFile=requirements.txt)
[![PyPI version shields.io](https://img.shields.io/pypi/v/test_junkie.svg)](https://pypi.python.org/pypi/test_junkie/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/test_junkie.svg)](https://pypi.python.org/pypi/test_junkie/)
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

## Key Features

> Not a wrapper around `unittest`. Every capability below ships with the library — no plugins to install, no config files to write, no external orchestrators.

- Decorator-based: `@Suite` and `@test` on plain Python classes — no base class to extend, no config file to maintain
- Lifecycle hooks: `@beforeClass`, `@afterClass`, `@beforeTest`, `@afterTest` — declared directly on the class
- Built-in parallel execution with independent thread limits at the suite tier (`-T`) and the test tier (`-S`) — opt-in per class and per test, no external orchestrator needed
- Exception-aware retries: `retry_on=[ConnectionError]` re-runs on infrastructure noise; `no_retry_on=[AssertionError]` ensures real bugs always surface
- Multi-layer parametrization: suite params × test params = every combination, each variant tracked and retried independently
- `Rules` class for shared lifecycle across suites — define hooks once, attach to many suites; one change propagates everywhere
- First-class `owner`, `component`, `tags`, and `priority` on every test — `tj run --tags smoke` in CI, full suite locally, no test-selection scripts to maintain
- Typed result objects via `runner.summary.suites` and live-firing `Listener(on_failure=...)` — build alerts and CI gates without a plugin system
- HTML, XML, and JSON reports after every run — no plugins, no config files, no post-processing step
- Full CLI: `tj run`, `tj audit`, `tj config` — run and inspect suites without writing a runner script

And [more →](https://www.test-junkie.com/documentation/)

## Installation

```
pip install test-junkie
```

## Getting Started

<p align="center">
  <a href="https://www.test-junkie.com/get-started/"><img src="https://img.shields.io/badge/Get%20Started-f37814?style=for-the-badge" alt="Get Started"></a>
  &nbsp;
  <a href="https://www.test-junkie.com/documentation/"><img src="https://img.shields.io/badge/Documentation-3a3f4b?style=for-the-badge" alt="Documentation"></a>
</p>

---

<p align="center">
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/Changelog-recent%20changes-3a3f4b?style=flat-square" alt="Changelog"></a>
  &nbsp;&nbsp;
  <a href="https://github.com/ArturSpirin/test_junkie/issues/new?template=bug_report.md"><img src="https://img.shields.io/badge/Bug%20Report-open%20an%20issue-b92c2c?style=flat-square" alt="Report a Bug"></a>
</p>
