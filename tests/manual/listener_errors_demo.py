"""
Manual check for 0.9a8: a listener that raises no longer ends its suite.

    python tests/manual/listener_errors_demo.py            all three suites
    python tests/manual/listener_errors_demo.py listeners  only the listener suites

What to look for:
- every suite runs every test - BrokenListenerSuite included (a listener raised on 3 of its calls)
- Problems lists a LISTENER entry per listener call that raised, with the listener's traceback
- the tests themselves keep their own results: all pass except check_the_cart, which fails on purpose
- with "listeners": the verdict reads "FAILED  3 listener calls failed" and run() raises TestListenerError once the
  summary is printed - the run is still a failure, it just isn't cut short
- SuiteThatDiesSuite: a test calls sys.exit(). The tests that suite never got to are IGNORED, not left out. The
  verdict names the first error of the run, so with all three suites it reads "run stopped by SystemExit"
"""
import sys
import time

from test_junkie.decorators import Suite, test
from test_junkie.listener import Listener
from test_junkie.runner import Runner


class FlakyReporter(Listener):

    def on_in_progress(self, **kwargs):
        if kwargs["properties"]["jm"]["jto"].get_function_name() == "log_in":
            raise ConnectionError("reporting service unavailable")

    def on_success(self, **kwargs):
        if kwargs["properties"]["jm"]["jto"].get_function_name() == "add_to_cart":
            raise KeyError("build_id")

    def on_failure(self, **kwargs):
        raise ValueError("could not upload the screenshot")


@Suite(listener=FlakyReporter, parallelized=True)
class BrokenListenerSuite:

    @test()
    def log_in(self):
        time.sleep(0.5)

    @test()
    def add_to_cart(self):
        time.sleep(0.5)

    @test()
    def check_the_cart(self):
        time.sleep(0.5)
        assert False, "cart is empty"

    @test(parameters=["visa", "amex", "paypal"])
    def check_out(self, parameter):
        time.sleep(0.3)


@Suite(parallelized=True)
class HealthySuite:

    @test()
    def search(self):
        time.sleep(1)

    @test()
    def browse(self):
        time.sleep(1)


@Suite(parallelized=True)
class SuiteThatDiesSuite:

    @test()
    def first(self):
        time.sleep(0.5)

    @test()
    def calls_sys_exit(self):
        sys.exit("a test called sys.exit()")

    @test(parameters=[1, 2, 3])
    def never_reached(self, parameter):
        pass


if __name__ == "__main__":
    suites = [BrokenListenerSuite, HealthySuite]
    if sys.argv[1:] != ["listeners"]:
        suites.append(SuiteThatDiesSuite)
    try:
        Runner(suites).run(suite_multithreading_limit=3)
    except BaseException as error:
        print("\nrun() raised {}: {}".format(type(error).__name__, error))
