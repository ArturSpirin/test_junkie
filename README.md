[![Build Status](https://travis-ci.com/ArturSpirin/test_junkie.svg?branch=master)](https://travis-ci.com/ArturSpirin/test_junkie) 
[![codecov](https://codecov.io/gh/ArturSpirin/test_junkie/branch/master/graph/badge.svg)](https://codecov.io/gh/ArturSpirin/test_junkie) 
[![Maintainability](https://api.codeclimate.com/v1/badges/40b17ed68d5b3eca140b/maintainability)](https://codeclimate.com/github/ArturSpirin/test_junkie/maintainability)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/ArturSpirin/test_junkie/graphs/commit-activity)
[![Known Vulnerabilities](https://snyk.io/test/github/ArturSpirin/test_junkie/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/ArturSpirin/test_junkie?targetFile=requirements.txt) 
[![PyPI version shields.io](https://img.shields.io/pypi/v/test_junkie.svg)](https://pypi.python.org/pypi/test_junkie/) 
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/test_junkie.svg)](https://pypi.python.org/pypi/test_junkie/)
[![Downloads](https://pepy.tech/badge/test-junkie)](https://pepy.tech/project/test-junkie)

# Test Junkie [![Twitter](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Checkout+this+new+awesome+test+runner+for+Python!&url=https%3A%2F%2Fgithub.com%2FArturSpirin%2Ftest_junkie&hashtags=github,python,programming,pythonprogramming&original_referer=http%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton)
[![Test Junkie Logo](https://www.test-junkie.com/static/media/logo.png)](https://www.test-junkie.com/)

## Installation

From your favorite terminal:

`pip install test-junkie` or `python -m pip install test-junkie`

## Basic Usage

Save code bellow into a Python file. Lets say `C:\Development\TestJunkie\demo.py`.
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
    # OR use Test Junkie's CLI: `tj run -s C:\Development\TestJunkie\demo.py`
```

## CLI

Starting from version `0.6a6` there is now full [CLI](https://www.test-junkie.com/documentation/#cli) 
support and the above test suite can also be executed with `tj run -s C:\Development\TestJunkie\demo.py`

For more examples, see [CLI documentation](https://www.test-junkie.com/documentation/#cli).

## Output Example
[![Test Junkie Console Output](https://www.test-junkie.com/static/media/console_out.jpg)](https://www.test-junkie.com/static/media/console_out.jpg)

Full documentation is available on **[test-junkie.com](https://www.test-junkie.com/)**  

Please [report](https://github.com/ArturSpirin/test_junkie/issues/new?template=bug_report.md) any bugs you find.

**Our Sponsors**

[<img width="270" src="https://www.actocorp.com/wp-content/uploads/2019/02/ActoLogo-red.png">](https://www.actocorp.com)

become our [sponsor](https://www.patreon.com/join/arturspirin?)
