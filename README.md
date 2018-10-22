## Test Junkie [alpha] [![Build Status](https://travis-ci.com/ArturSpirin/test_junkie.svg?branch=master)](https://travis-ci.com/ArturSpirin/test_junkie) [![Maintainability](https://api.codeclimate.com/v1/badges/40b17ed68d5b3eca140b/maintainability)](https://codeclimate.com/github/ArturSpirin/test_junkie/maintainability) <a href="https://codeclimate.com/github/ArturSpirin/test_junkie/test_coverage"><img src="https://api.codeclimate.com/v1/badges/40b17ed68d5b3eca140b/test_coverage" /></a>

Test Junkie is a classy framework for executing test scenarios. Designed to be simple and intuitive so any beginner 
can get started while delivering many features that are desired by high end test engineers.

_This is a pre-release version, documentation may be incomplete and functionality of features is subject to change._

## Table of  content

* [Installation](#installation)
* [Features](#features)
  * [Decorators](#decorators)
    * [@Suite](#suite)
    * [@beforeClass](#beforeclass)
    * [@beforeTest](#beforetest)
    * [@test](#test)
    * [@afterTest](#aftertest)
    * [@afterClass](#afterclass)
  * [Skipping Tests/Suites](#skipping-testssuites)
  * [Retrying Tests/Suites](#retrying-testssuites)
  * [Parameterized Tests](#parameterized-tests)
  * [Parameterized Suites](#parameterized-suites)
  * [Parallel Test/Suite Execution](#parallel-test-execution)
    * [Restricting Parallel Execution](#restricting-parallel-execution-at-suitetest-level)
  * [Test Listeners](#test-listeners)
    * [On Success](#on-success)
    * [On Fail](#on-fail)
    * [On Error](#on-error)
    * [On Ignore](#on-ignore)
    * [On Cancel](#on-cancel)
    * [On Skip](#on-skip)
    * [On Class Skip](#on-class-skip)
    * [On Class Cancel](#on-class-cancel)
    * [On Before Class Fail](#on-before-class-failure)
    * [On Before Class Error](#on-before-class-error)
    * [On After Class Fail](#on-after-class-failure)
    * [On After Class Error](#on-after-class-error)
  * [Meta](#meta)
  * [Rules](#rules)
  * [Tags](#tags)
* [Examples](#examples)
  * [Test Suite](#test-suite)
  * [Running Test Suite(s)](#executing-test-suites)
    * [Using Runner with Tags](#executing-with-tags)
    * [Using parallel execution](#using-parallel-test-execution)
    * [Canceling test execution](#canceling-test-execution)

## Installation
`pip install test_junkie`
##
## Features
### Decorators
#### @Suite
Test Junkie enforces suite based test architecture. Thus all tests must be defined within a class and 
that class must be decorated with @Suite. See example on [Test Suites](#test-suite). 
```python
from test_junkie.decorators import Suite

@Suite()
class LoginFunctionality:
    ...
```
@Suite decorator supports the following decorator properties:
+ [Meta](#meta): `@Suite(meta=meta(name="Suite Name"))`
+ [Retry](#retrying-testssuites): `@Suite(retry=2)` 
+ [Skip](#skipping-testssuites): `@Suite(skip=Boolean)` 
+ [Listeners](#test-listeners): `@Suite(listener=YourListener)`
+ [Rules](#rules): `@Suite(rules=YourRules)`
+ [Parallel Restriction](#restricting-parallel-execution-at-suitetest-level): `@Suite(pr=[ATestSuite])`
+ [Parallelized](#restricting-parallel-execution-at-suitetest-level): `@Suite(parallelized=False)`

#### @beforeClass
This decorator will prioritize execution of a decorated function at the very beginning of a test suite.
Decorated function will be executed only once at the very beginning of the test suite. Code which produces exception in 
the decorated function will be treated as a class failure which will mark all of the tests in the suite as ignored. 
[On Ignore](#on-ignore) event listener will be called for each of the tests.
```python
from test_junkie.decorators import beforeClass

...
@beforeClass()
def a_function():
    ...
```
@beforeClass does not support any special decorator properties.

#### @beforeTest
This decorator will prioritize execution of a decorated function before every test case in the suite.
Decorated function will be executed once before every test case in the suite. Code which produces exception in the
decorated function will be treated as a test failure/error and respective [On Error](#on-error) or 
[On Fail](#on-fail) event listener will be called.
```python
from test_junkie.decorators import beforeTest

...
@beforeTest()
def b_function():
    ...
```
@beforeTest does not support any special decorator properties.

#### @test
Test Junkie enforces suite based test architecture. Thus all tests must be defined within a class and be decorated 
with @test. See example on [Test Suites](#test-suite). Code which produces exception in the
decorated function will be treated as a test failure/error and respective [On Error](#on-error) or 
[On Fail](#on-fail) event listener will be called. Function decorated with [@afterTest](#aftertest) will not be 
executed if exception is raised in a test case. [On Success](#on-success) event listener will be called if test passes.
```python
from test_junkie.decorators import test

...

@test()
def a_test():
    ...

@test()
def b_test():
    ...
```
@test decorator supports the following decorator properties: 
+ [Meta](#meta): `@test(meta=meta(name="Test Name", known_bugs=[12345, 34567]))`
+ [Retry](#retrying-testssuites): `@test(retry=2)` 
+ [Skip](#skipping-testssuites): `@test(skip=Boolean)` 
+ [Parameters](#parameterized-tests): `@test(parameters=[1, 2, 3, 4])`
+ [Parallelized](#restricting-parallel-execution-at-suitetest-level): `@test(parallelized=False)`
+ [Parallelized Parameters](#restricting-parallel-execution-at-suitetest-level): `@test(parallelized_parameters=True)`

#### @afterTest
This decorator will de-prioritize execution of a decorated function for the end of each test case in the suite.
Decorated function will be executed once after every test cases in the suite. Code which produces exception in the
decorated function will be treated as a test failure/error and respective [On Error](#on-error) or 
[On Fail](#on-fail) event listener will be called.
```python
from test_junkie.decorators import afterTest

...
@afterTest()
def c_function():
    ...
```
@afterTest does not support any special decorator properties.

#### @afterClass
This decorator will de-prioritize execution of a decorated function for the very end of a test suite.
Decorated function will be executed only once at the very end of the test suite.
```python
from test_junkie.decorators import afterClass

...
@afterClass()
def d_function():
    ...
```
@afterClass does not support any special decorator properties.

### Skipping Tests/Suites
Test Junkie extends skipping functionality at the test level and at the suite level. You can use both at the same time 
or individually.
```python
from test_junkie.decorators import Suite, test

@Suite()
class ExampleSuite:

    @test(skip=True)
    def a_test(self):
    
        assert True is False
```
+ Test level skip takes a boolean value, if True - test will be skipped and [On Skip](#on-skip) event listener will be 
called. Execution of tests will continue as usual if there are any remaining tests in the suite.
+ Test level skip can also take a function as `my_function` or `my_function()` in the earlier, it will 
evaluate the function prior to running the test while the later will evaluate as soon at your suite is imported 
anywhere in your code.
    + If your function has `meta` argument in the signature, Test Junkie will pass all of the test function's 
    [Meta](#meta) information to it. All of this support is there in order to ensure that you have maximum flexibility 
    to build custom business logic for skipping tests.
    + The only requirement is, function must return `boolean` value when evaluation completes.

```python
from test_junkie.decorators import Suite, test

@Suite(skip=True)
class ExampleSuite:

    @test()
    def a_test(self):
    
        assert True is False
```
+ Suite level skip takes a boolean value, if True - all of the decorated functions in the suite will be skipped. 
[On Skip](#on-skip) event listener will NOT be called, instead [On Class Skip](#on-class-skip) will fire.

### Retrying Tests/Suites
Test Junkie extends retry functionality at the test level and at the suite level. You can use both at the same time 
or individually. Code bellow uses both, test and suite, level retries.
```python
from test_junkie.decorators import Suite, test

@Suite(retry=2)
class ExampleSuite:

    @test(retry=2)
    def a_test(self):
    
        assert True is False
```
+ Test level retry will retry the test, until test passes or retry limit is reached, immediately after the failure. 
+ Suite level retry will kick in after all of the tests in the suite have been executed and there is at least one 
unsuccessful test. Test level retries will be honored again during the suite retry. 
Only unsuccessful tests will be retried.

With that said, the above test case will be retried 4 times in total.

### Parameterized Tests
Test Junkie allows you to run parameterized test scenarios out of the box and it allows all data types to be 
used as parameters.
```python
from test_junkie.decorators import Suite, test

@Suite()
class ExampleSuite:

    @test(parameters=[{"fruits": ["apple", "peach"]}, None, "blue", [1, 2, 3]])
    def a_test(self, parameter):
    
        print("Test parameter: {}".format(parameter)) 
```
+ Any time parameterized test is defined, the decorated function must accept `parameter` in the function signature.
+ If parameterized test fails and [retry](#retrying-testssuites) is used, only the parameter(s) that test failed 
with will be [retried](#retrying-testssuites).

### Parameterized Suites
There is a slightly different spin, suite level parameters can apply to all of the decorated functions in the suite. 
You can control in which functions or tests to use them. In the functions, where you want to use suite level 
parameters, add `suite_parameter` to the function's signature:
```python
from test_junkie.decorators import Suite, test, beforeClass, beforeTest

@Suite(parameters=[{"fruits": ["apple", "peach"]}, None, "blue", [1, 2, 3]])
class ExampleSuite:

    @beforeClass()
    def before_class(self, suite_parameter):
        print("Before Class with suite parameter: {}".format(suite_parameter))
        
    @beforeTest()
    def before_test(self, suite_parameter):
        print("Before Test with suite parameter: {}".format(suite_parameter))

    @test()
    def a_test(self, suite_parameter):
    
        print("Suite parameter: {}".format(suite_parameter))
        
    @test(parameters=[1, 2, 3])
    def a_test(self, parameter, suite_parameter):
    
        print("Test parameter: {}".format(parameter))
        print("Suite parameter: {}".format(suite_parameter))
```
+ Suite level parameters can be used at the same time with [test level parameters](#parameterized-tests).
+ If parameterized test fails and [retry](#retrying-testssuites) is used, only the parameter(s) that test failed 
with will be [retried](#retrying-testssuites) - yes this applies to the suite level parameters as well.

### Parallel Test Execution
Test Junkie supports parallel execution out of the box. Two modes are available and both can be used at the same time:
+ `suite_multithreading`: Allows to run `N` number of suites in parallel. Default is 1.
+ `test_multithreading`: Allows to run `N` number of test cases in parallel. Default is 1.

`N` is the limit of threads that you want to use, it can be defined using arguments that are passed to the `run()` 
function of the `Runner` instance.
+ `suite_multithreading_limit`: Use to define max number of suites to run in parallel. By default it will use one 
thread, which means suites wont be running in parallel until you set value greater than 1.
+ `test_multithreading_limit`: Use to define max number of suites to run in parallel. By default it will use one 
thread, which means tests wont be running in parallel until you set value greater than 1.

#### Restricting Parallel Execution at Suite/Test level

Restrict parallel execution at the suite level: 
- Lets say you have suites: `A`, `B`, `C` and suite `A` 
can have a conflict with suite `C` if it runs in parallel. Using the property `pr` (stands for parallel restriction) 
from the [@Suite](#suite) decorator which takes a list of class objects, you can let Test Junkie know that you 
don't want to run those suites in parallel.
    ```python
    from my_suite.C import C
    from test_junkie.decorators import Suite
    
    @Suite(pr=[C])
    class A:
      ...
    ```
    Parallel restriction is bidirectional, meaning you only need to set it in `A` or `C` - not both (although you can, 
    but that will most likely lead to import loop). Assuming you set it in `A`. When time comes to run suite `A`, Test 
    Junkie will check to make sure that suite `C` is not running. Similar, when time comes to run suite `C`, Test Junkie 
    will check to make sure suite `A` is not running, even though you did not set the restriction explicitly in 
    suite `C` to avoid suite `A`.
- If you flat out don't want to run a suite in parallel with any other suites, you can also set `parallelized` 
property of the [@Suite](#suite) decorator to `False`.

Restricting parallel execution at the test level:
- Parameterized tests can be executed in multi threaded mode as well and this limit applies to tests with 
parallelized parameters. By default `paralellized_parameters` mode is set off, but you can turn it on 
via the [@test](#test) decorator properties.
- Its possible that some tests could conflict with others when ran in parallel, for this reason all of the test 
cases have individually controlled parallelized mode via `parallelized` [@test](#test) 
decorator property. What this means: When Test Junkie reaches a test in parallelized mode that 
has individual parallelized mode set to False, Test Junkie will wait for all of the currently parallelized 
tests to finish before running that one test.

For usage examples see [Using Parallel Execution](#using-parallel-test-execution). 

### Test Listeners
Test Junkie allows you to define test listeners which allow to execute your own code on a specific test event. 
Defining listeners is optional. This feature is typically useful when building large frameworks as it allows for 
seamless integration for reporting, post processing of errors, calculation of test metrics, alerts, 
artifact collection etc.

Listeners that you want to use are defined at the suite level and are supported by the [@Suite](#suite) decorator. 
This allows flexibility to support different types of tests without having to add complexity every time 
you need to support a new type of test.

In order to create a test listener you need to create a new class and inherit from `TestListener`. 
After that, you can overwrite functions that you wish to support. 

Following test functions can be overwritten: 
+ [On Success](#on-success)
+ [On Fail](#on-fail) 
+ [On Error](#on-error) 
+ [On Ignore](#on-ignore) 
+ [On Skip](#on-skip)
+ [On Cancel](#on-cancel)

Following class(suite) functions can be overwritten:
+ [On Before Class Failure](#on-before-class-failure)
+ [On Before Class Error](#on-before-class-error)
+ [On After Class Failure](#on-after-class-failure) 
+ [On After Class Error](#on-after-class-error) 
+ [On Class Skip](#on-class-skip)
+ [On Class Cancel](#on-class-cancel)

```python
from test_junkie.listener import Listener

class MyTestListener(Listener):

    def __init__(self, **kwargs):

        Listener.__init__(self, **kwargs)
    ...
```
#### On Success
On success event is triggered after test has successfully executed, that means [@beforeTest](#beforetest) (if any), 
[@test](#test), and [@afterTest](#aftertest) (if any) decorated functions have ran without producing an exception.
```python
...
    def on_success(self, properties):
        # Write your own code here
        print(properties) 
    ...
```

#### On Fail
On failure event is triggered after test has produced `AssertionError`. `AssertionError` must be unhandled and  
thrown during the code execution in functions decorated with [@beforeTest](#beforetest) (if any), [@test](#test), 
or [@afterTest](#aftertest) (if any). Make sure to include `exception` argument in the method signature, Exception 
object will be accessible through this argument.
```python
...
    def on_failure(self, properties, exception):
        # Write your own code here
        print(properties) 
    ...
```

#### On Error
On error event is triggered after test has produced any exception other than `AssertionError`. Exception must be 
unhandled and thrown during the code execution in functions decorated with [@beforeTest](#beforetest) (if any), 
[@test](#test), or [@afterTest](#aftertest) (if any). Make sure to include `exception` argument in the method signature, 
Exception object will be accessible through this argument.
```python
...
    def on_error(self, properties, exception):
        # Write your own code here
        print(properties) 
    ...
```

#### On Ignore
On ignore event is triggered when a function decorated with [@beforeClass](#beforeclass) 
produces an exception. In this unfortunate event, all of the tests under that particular test suite will be marked 
ignored. Make sure to include `exception` argument in the method signature, Exception object will be accessible 
through this argument. 

On ignore event can also be triggered when incorrect arguments are passed to the [@test](#test) decorator.
```python
...
    def on_ignore(self, properties, exception):
        # Write your own code here
        print(properties)
    ...
```

#### On Skip
On skip event is triggered, well, when tests are skipped. Skip is supported by [@test](#test) & [@Suite](#suite) 
function decorators. See [Skipping Tests/Suites](#skipping-testssuites) for examples. 
Skip event can also be triggered when [Using Runner with tags](#executing-with-tags).
```python
...
    def on_skip(self, properties):
        # Write your own code here
        print(properties)
    ...
```

#### On Cancel
On Cancel event is triggered _sometime_* after `cancel()` is called on the active `Runner` object.
See [Canceling test execution](#canceling-test-execution) for more info. 
It is not guaranteed that this event will be called, however. Assuming that, `cancel()` was called while `Runner` is 
in the middle of processing a test suite, yes it will be called on all of the remaining tests that have not yet 
been executed. All of the previously executed tests wont be effected. Tests in the following suites wont be marked 
canceled neither, the suites will be "skipped" if you will but [On Class Cancel](#on-class-cancel) will be called on 
all of the suites.
```python
...
    def on_cancel(self, properties):
        # Write your own code here
        print(properties)
    ...
```

#### On Class Skip
On Class Skip event is triggered, when test suites are skipped. Skip is supported by [@test](#test) & [@Suite](#suite) 
function decorators. See [Skipping Tests/Suites](#skipping-testssuites) for examples.
```python
...
    def on_class_skip(self, properties):
        # Write your own code here
        print(properties) 
    ...
```

#### On Class Cancel
On Class Cancel event is triggered _sometime_* after `cancel()` is called on the active `Runner` object. 
See [Canceling test execution](#canceling-test-execution) for more info. 

Event will apply only to those suites that are executed in scope of that `Runner` object, 
see [Running Test Suite(s)](#executing-test-suites) for more info.

```python
...
    def on_class_cancel(self, properties):
        # Write your own code here
        print(properties) 
    ...
```

#### On Before Class Failure
On Before Class Failure event is triggered only when a function decorated with [@beforeClass](#beforeclass) 
produces `AssertionError`. Make sure to include `exception` argument in the method signature, Exception object will be 
accessible through this argument. [On Ignore](#on-ignore) will also fire.
```python
...
    def on_before_class_failure(self, properties, exception):
        # Write your own code here
        print(properties) 
    ...
```

#### On Before Class Error
On Before Class Error event is triggered only when a function decorated with [@beforeClass](#beforeclass) 
produces exception other than `AssertionError`. Make sure to include `exception` argument in the method signature, 
Exception object will be accessible through this argument. [On Ignore](#on-ignore) will also fire.
```python
...
    def on_before_class_error(self, properties, exception):
        # Write your own code here
        print(properties) 
    ...
```


#### On After Class Failure
On After Class Failure event is triggered only when a function decorated with [@afterClass](#afterclass) 
produces `AssertionError`. Make sure to include `exception` argument in the method signature, Exception object will be 
accessible through this argument. No test level event listeners will be fired.
```python
...
    def on_after_class_failure(self, properties, exception):
        # Write your own code here
        print(properties) 
    ...
```

#### On After Class Error
On After Class Error event is triggered only when a function decorated with [@afterClass](#afterclass) 
produces exception other than `AssertionError`. Make sure to include `exception` argument in the method signature, 
Exception object will be accessible through this argument. No test level event listeners will be fired.
```python
...
    def on_after_class_error(self, properties, exception):
        # Write your own code here
        print(properties) 
    ...
```


#### Meta
All of the TestListener class instance functions have access to the test's and suite's meta information if such 
was passed in to the [@Suite](#suite) or [@test](#test) decorator. Metadata can be of any data type. 
You can use meta to set properties such as:
+ Test name, suite name, description, expected results etc - anything that can be useful in reporting
+ Test case IDs - if you have a test management system, leverage it to link test scripts directly 
to the test cases and further integrations can be implemented from there
+ Bug ticket IDs - if you have a bug tracking system, leverage it to link your test case with issues that are already 
known and allow you to process failures in a different manner and/or allow for other integrations with the 
tracking system
```python
from test_junkie.decorators import Suite, test


@Suite(listener=MyTestListener, 
       meta={"name": "Your suite name", 
             "id": 123444})
class ExampleSuite:

    @test(meta={"name": "You test name", 
                "id": 344123, 
                "known_bugs": [11111, 22222, 33333], 
                "expected": "Assertion must pass"})
    def a_test(self):
    
        assert True is True
```
Metadata that was set in the code above can be accessed in any of the event listeners like so:
```python
from test_junkie.listener import Listener


class MyTestListener(Listener):

    def __init__(self, **kwargs):

        Listener.__init__(self, **kwargs)

    def on_success(self, properties):
        
        print("Suite name: {name}".format(name=properties["class_meta"]["name"]))
        print("Suite ID: {id}".format(id=properties["class_meta"]["id"]))
        print("Test name: {name}".format(name=properties["test_meta"]["name"]))
        print("Test ID: {id}".format(id=properties["test_meta"]["id"]))
        print("Expected result: {expected}".format(expected=properties["test_meta"]["expected"]))
        print("Known bugs: {bugs}".format(bugs=properties["test_meta"]["known_bugs"]))
```
Meta information can be updated and/or added from within your test cases using the `Meta.update()` function.
Keep in mind, only test level meta can be updated - suite level meta should never change.
`Meta.update()` takes 2 positional arguments:
- `parameter`: (optional) this is the current parameter that the test is running with. 
If test case is not parameterized, do not pass anything.
- `suite_parameter`: (optional) this is the current [suite parameter](#parameterized-suites) that the test is running 
with. If test case is not parameterized with suite level parameters, do not pass anything.

Any other arguments that are passed in to the function, will be pushed to the meta definition.

All of the meta updates will be available from the [listeners](#test-listeners) just like the rest of the meta 
definition if such was hard coded within the [@test](#test) decorator.
```python
from test_junkie.decorators import test
from test_junkie.meta import Meta
...
@test()
def a_test(self):
    ...
    Meta.update(name="new test name", expected="updated expectation")
    ...
    
@test(parameters=[1, 2, 3])
def b_test(self, parameter):
    ...
    Meta.update(parameter=parameter, name="new test name", expected="updated expectation")
    ...
    
@test(parameters=[1, 2, 3])
def c_test(self, parameter, suite_parameter):
    ...
    Meta.update(parameter=parameter, suite_parameter=suite_parameter,
                name="new test name", expected="updated expectation") 
    ...
```

#### Rules
You may have a situation where you find your self copy pasting code from one suite's @beforeClass or @beforeTest 
function(s) into another. Test Junkie allows you to define Rules in such cases. Rule definitions are reusable, similar 
to the [Listeners](#test-listeners) and also supported by the [@Suite](#suite) decorator.

In order to create Rules, you need to create a new class and inherit from `TestRules`. 
After that, you can overwrite functions that you wish to use.
```python
from test_junkie.rules import Rules

class MyRules(Rules):

    def __init__(self, **kwargs):

        Rules.__init__(self, **kwargs)

    def before_class(self):
        # write your code here
        pass

    def before_test(self):
        # write your code here
        pass

    def after_test(self):
        # write your code here
        pass

    def after_class(self):
        # write your code here
        pass
```

To use the Rules you just created, reference them in the suite definition:
```python
from test_junkie.decorators import Suite


@Suite(rules=MyRules)
class ExampleSuite:
...
```
Execution priority vs the [Decorators](#decorators):
+ `before_class()` will run right before the function decorated with [@beforeClass](#beforeclass).
+ `before_test()` will run right before the function decorated with [@beforeTest](#beforetest).
+ `after_test()` will run right after the function decorated with [@afterTest](#aftertest).
+ `after_class()` will run right after the function decorated with [@afterClass](#afterclass).

Failures/Exceptions, produced inside this functions, will be treated similar to their respective 
[Decorators](#decorators).


#### Tags
Test Junkie allows you to tag your test scenarios. You can use the tags to run or skip test cases that match the tags 
when you run your tests. Following tag configurations are supported:
+ `run_on_match_all` - Will run test cases that match all of the tags in the list. 
                       Will trigger [On Skip](#on-skip) event for all of the tests that do not match the tags 
                       or do not have tags.
+ `run_on_match_any` - Will run test cases that match at least one tag in the list
                       Will trigger [On Skip](#on-skip) event for all of the tests that do not match the tags 
                       or do not have tags.
+ `skip_on_match_all` - Will skip test cases that match all of the tags in the list. 
                        Will trigger [On Skip](#on-skip) event.
+ `skip_on_match_any` - Will skip test cases that match at least one tag in the list. 
                        Will trigger [On Skip](#on-skip) event.

All of the configs can be used at the same time. However, this is the order that will be honored:
 
`skip_on_match_all` -> `skip_on_match_any` -> `run_on_match_all` -> `run_on_match_any` 
which ever matches first will be executed or skipped. 

See [Using Runner with Tags](#executing-with-tags) for usage examples.

### Examples
#### Test Suite
```python
from random import randint
from test_junkie.decorators import test, Suite, beforeTest, beforeClass, afterTest, afterClass
from test_junkie.meta import meta
from example_package.example_listener import ExampleListener

# Listener here is optional as all of the other parameters
@Suite(listener=ExampleListener, retry=2, 
       meta=meta(suite_name="Demo Suite"))
class ExampleTestSuite(object):

    @beforeClass()
    def before_class(self):  # Functions are not restricted to any naming conventions
        print("BEFORE CLASS!")
        
    @beforeTest()
    def before_test(self):
        print("BEFORE TEST!")

    @afterTest()
    def after_test(self):
        print("AFTER TEST!")

    @afterClass()
    def after_class(self):
        print("AFTER CLASS!")
    
    # meta function is used for metadata, slightly cleaner then using a dict
    # all parameters are optional
    @test(parameters=[1, 2, 3, 4, 5], retry=2,
          meta=meta(name="Test 'A'",
                    test_id=344941,
                    known_bugs=[],
                    expected="Assertion must pass"), 
          tags=["component_a", "critical"])
    def a_test(self, parameter):  # Functions are not restricted to any naming conventions
        print("TEST 'A', param: ", parameter)
        assert randint(1, 5) == parameter, "your error message"

    # regular dict is used for metadata
    @test(meta={"name": "Test 'B'",
                "test_id": 344123,
                "known_bugs": [11111, 22222, 33333],
                "expected": "Assertion must pass"},
          tags=["component_a", "trivial", "known_failure"])
    def b_test(self):
        print("TEST 'B'")
        assert True is True

    @test(skip=True)
    def c_test(self):
        print("TEST 'C'")
```

#### Executing Test Suites
Use the `run()` function from the `Runner` instance to start running tests. `run()` supports a number of properties:
+ `tag_config`: allows to run tests that conforms to the tags, 
see [Executing with Tags](#executing-with-tags) for more info.
+ `suite_multithreading`: Enables multithreading at suite level, 
see [Using Parallel Test Execution](#using-parallel-test-execution) for more info.
+ `suite_multithreading_limit`: Sets thread limit for multithreading at suite level, 
see [Using Parallel Test Execution](#using-parallel-test-execution) for more info.
+ `test_multithreading`: Enables multithreading at test level, 
see [Using Parallel Test Execution](#using-parallel-test-execution) for more info.
+ `test_multithreading_limit`: Sets thread limit for multithreading at test level, 
see [Using Parallel Test Execution](#using-parallel-test-execution) for more info.

```python
from test_junkie.runner import Runner
from example_package.example_test_suite import ExampleTestSuite

runner = Runner([ExampleTestSuite])
runner.run()
```

##### Executing with Tags
`TestRunner.run()` supports `tag_config` keyword that defines the configuration you want to use for the tags. 
All of the supported configurations as well as honor priority are defined in the [Tags](#tags) section.
```python
runner.run(tag_config={"run_on_match_all": ["component_a", "critical"]})
```
```python
runner.run(tag_config={"skip_on_match_any": ["trivial", "known_failure"]})
```

##### Using Parallel Test Execution
Will enable multithreading for suites and tests, but by default both will use 1 thread each:
```python
runner = Runner([ExampleTestSuite, ExampleTestSuite2])
runner.run(suite_multithreading=True, test_multithreading=True)
```

Will enable multithreading for suites and tests but allows to run maximum of 5 suites and up to 2 tests per suite 
in parallel:
```python
runner = Runner([ExampleTestSuite, ExampleTestSuite2])
runner.run(suite_multithreading=True, suite_multithreading_limit=5, 
           test_multithreading=True, test_multithreading_limit=2)
```
Of course, you can set any limits that your system can handle or that otherwise make sense.
 
For more info,  see [Parallel Test/Suite Execution](#parallel-test-execution).

##### Canceling Test Execution
If you are integrating Test Junkie into a bigger framework, its possible that you would like to programmatically stop 
test execution. Good news that Test Junkie allows, gracefully, to do just that. If you call `cancel()` on the `Runner`
Object, the Runner will start marking tests and suites as canceled, which will trigger respective event listeners: 
+ [On Cancel](#on-cancel)
+ [On Class Cancel](#on-class-cancel)

Canceling execution, does not abruptly stop the `Runner` - all of the suites will still "run" but it will be similar to 
skipping which will allow suites & tests to quickly, but in their natural fashion, finish running without locking up 
any of the resources on the machine where it runs.
```python
runner.cancel()
```