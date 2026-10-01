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
  <em>Built because the alternatives made you choose.</em>
</p>

# Test Junkie [![Twitter](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Test+Junkie+is+one+of+the+most+powerful+testing+frameworks+on+Python+that+you+did+not+hear+of+and+you+are+missing+out!&url=https%3A%2F%2Ftest-junkie.com&hashtags=automation,testing,python&original_referer=https%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton)

## Key Features

- Parallel execution at both the suite and test level, with fine-grained thread limits and restrictions
- Built-in retry logic (`retry`, `retry_on`, `no_retry_on`) and parameterized suites/tests
- Run exactly what you want by tag, feature, component, owner, or priority — from Python or the CLI
- Reusable `Rules` (shared before/after logic across suites) and `Group Rules` (hooks that run once for a whole group of suites) — both distinct from the simpler per-suite `@beforeClass`/`@beforeTest` decorators
- Custom event listeners, plus per-test metadata you can read and update at runtime
- A real CLI (`tj run`, `tj audit`, `tj config`) for running and auditing suites without writing a runner script
- HTML and XML reports, plus optional CPU/memory resource monitoring during a run

## Installation

From your favorite terminal:

`pip install test-junkie` or `python -m pip install test-junkie`

Supports the latest stable Python release plus the five prior minor versions. See the
[pyversions badge](https://pypi.python.org/pypi/test_junkie/) above for the exact list currently published.

## Basic Usage

Save the code below into a Python file. Let's say `demo.py`.
```python
from test_junkie.decorators import Suite, beforeTest, afterTest, test, beforeClass, afterClass


@Suite()
class ExampleTestSuite:

    @beforeClass()
    def before_class(self):
        print("Hi, I'm before class")

    @beforeTest()
    def before_test(self):
        print("Hi, I'm before test")

    @afterTest()
    def after_test(self):
        print("Hi, I'm after test")

    @afterClass()
    def after_class(self):
        print("Hi, I'm after class")

    @test()
    def something_to_test1(self):
        print("Hi, I'm test #1")

    @test()
    def something_to_test2(self):
        print("Hi, I'm test #2")

    @test()
    def something_to_test3(self):
        print("Hi, I'm test #3")


# and to run this marvel programmatically, all you need to do . . .
if "__main__" == __name__:
    from test_junkie.runner import Runner
    runner = Runner([ExampleTestSuite])
    runner.run()
    # OR use Test Junkie's CLI: `tj run -s demo.py`
```

## CLI

Test Junkie has full [CLI](https://www.test-junkie.com/documentation/#cli) support, and the above
test suite can also be executed with `tj run -s demo.py`

For more examples, see [CLI documentation](https://www.test-junkie.com/documentation/#cli).

## Output Example
[![Test Junkie Console Output](https://www.test-junkie.com/static/media/console_out.jpg)](https://www.test-junkie.com/static/media/console_out.jpg)

### Full documentation is available on **[test-junkie.com](https://www.test-junkie.com/)**  

#### See [CHANGELOG.md](CHANGELOG.md) for recent changes.

#### Please [report](https://github.com/ArturSpirin/test_junkie/issues/new?template=bug_report.md) any bugs you find.
