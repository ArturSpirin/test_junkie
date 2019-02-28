[![Build Status](https://travis-ci.com/ArturSpirin/test_junkie.svg?branch=master)](https://travis-ci.com/ArturSpirin/test_junkie) 
[![codecov](https://codecov.io/gh/ArturSpirin/test_junkie/branch/master/graph/badge.svg)](https://codecov.io/gh/ArturSpirin/test_junkie) 
[![Maintainability](https://api.codeclimate.com/v1/badges/40b17ed68d5b3eca140b/maintainability)](https://codeclimate.com/github/ArturSpirin/test_junkie/maintainability)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/ArturSpirin/test_junkie/graphs/commit-activity) 
[![PyPI version shields.io](https://img.shields.io/pypi/v/test_junkie.svg)](https://pypi.python.org/pypi/test_junkie/) 
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/test_junkie.svg)](https://pypi.python.org/pypi/test_junkie/)
[![Known Vulnerabilities](https://snyk.io/test/github/ArturSpirin/test_junkie/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/ArturSpirin/test_junkie?targetFile=requirements.txt)
[![Downloads](https://pepy.tech/badge/test-junkie)](https://pepy.tech/project/test-junkie)


[![Test Junkie Logo](https://www.test-junkie.com/static/media/logo.png)](https://www.test-junkie.com/)

**Basic Usage**

Save code bellow into a Python file. Lets say `C:\Development\TestJunkie\demo.py`.
```python
from test_junkie.decorators import Suite, beforeTest, afterTest, test, beforeClass, afterClass
from test_junkie.runner import Runner


@Suite()
class ExampleTestSuite:
    
    @beforeClass()
    def before_class(self):
        pass
        
    @beforeTest()
    def before_test(self):
        pass
        
    @afterTest()
    def after_test(self):
        pass
        
    @afterClass()
    def after_class(self):
        pass
        
    @test()
    def something_to_test1(self):
        pass
        
    @test()
    def something_to_test2(self):
        pass
        
    @test()
    def something_to_test3(self):
        pass
        
        
# and to run this marvel, all you need to do . . .
if "__main__" == __name__:
    runner = Runner([ExampleTestSuite])
    runner.run()
```

You can either run this suite via your favourite IDE or via the CMD like you would run any other Python program.

**Output Example**
[![Test Junkie Console Output](https://www.test-junkie.com/static/media/console_out.jpg)](https://www.test-junkie.com/static/media/console_out.jpg)

Full documentation is available on **[test-junkie.com](https://www.test-junkie.com/)**  

Please [report](https://github.com/ArturSpirin/test_junkie/issues/new?template=bug_report.md) any bugs you find.

**Teaser**

[![test junkie teaser](https://www.test-junkie.com/static/media/test-junkie-teaser-trailer-play.jpg)](https://www.youtube.com/watch?v=vRrpOgbuT9w)
