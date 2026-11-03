import sys

from test_junkie.decorators import Suite, test
from test_junkie.shortcuts import skip
from tests.junkie_suites import report_correctness_checks


@Suite()
class ReportCorrectnessSuite:

    @test(parameters=report_correctness_checks.CHECKS)
    def report_correctness(self, parameter):
        # TJ has no xfail: a check that fails today on a known bug is skipped with its task key. The console shows no
        # skip reasons and holds the test's stdout, so the reason goes to the real stderr too
        reason = getattr(parameter, "known_bug", None)
        if reason is None and getattr(parameter, "needs_browser", False):
            reason = report_correctness_checks.browser_missing()
        if reason:
            sys.__stderr__.write("SKIPPED {}: {}\n".format(parameter.__name__, reason))
            sys.__stderr__.flush()
            skip(reason)
        parameter()
