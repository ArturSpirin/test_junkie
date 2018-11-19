from test_junkie.decorators import Suite, test, beforeClass, beforeTest, afterTest, afterClass
from test_junkie.meta import meta, Meta
from tests.junkie_suites.TestListener import TestListener
from tests.junkie_suites.TestRules import TestRules


@Suite(retry=2,
       listener=TestListener,
       rules=TestRules,
       meta=meta(name="Advanced Use Cases",
                 known_bugs=[]),
       parameters=[1, 2])
class AdvancedSuite:

    @beforeClass()
    def before_class(self, suite_parameter):
        pass

    @beforeTest()
    def before_test(self, suite_parameter):
        pass

    @afterTest()
    def after_test(self, suite_parameter):
        pass

    @afterClass()
    def after_class(self, suite_parameter):
        pass

    @test(retry=2, parameters=[10, 20], tags=["critical", "v1"],
          meta=meta(name="No Retry", expected="Test must pass on 1st go, thus should not be retried"))
    def no_retry(self, parameter, suite_parameter):
        assert parameter is not None
        assert suite_parameter is not None
        Meta.update(parameter=parameter, suite_parameter=suite_parameter,
                    name="No Retry 1", expected="updated")

    @test(retry=2, parameters=[10, 20], tags=["critical", "v1"], parallalized_parameters=True,
          meta=meta(name="No Retry", expected="Test must pass on 1st go, thus should not be retried"))
    def no_retry2(self, parameter):
        assert parameter is not None
        Meta.update(parameter=parameter, name="No Retry 2", expected="updated")

    @test(retry=2, tags=["critical", "v1"],
          meta=meta(name="No Retry", expected="Test must pass on 1st go, thus should not be retried"))
    def no_retry3(self, suite_parameter):
        assert suite_parameter is not None
        Meta.update(suite_parameter=suite_parameter, name="No Retry 3", expected="updated")

    @test(retry=2, tags=["critical2"])
    def retry(self):
        Meta.update(name="Retry", expected="Updated for Retry")
        assert True is False, "Expected Assertion Error"

    @test(retry=2, tags=["trivial"])
    def retry2(self):
        Meta.update(name="new test name", expected="updated expectation")
        assert True is False, "Expected Assertion Error 2"

    @test(retry=2, parameters=[10, 20], tags=["critical", "v1"],
          meta=meta(name="Retry 3", expected="Test must fail and be retried"))
    def retry3(self, parameter, suite_parameter):
        assert parameter is not None
        assert suite_parameter is not None
        Meta.update(parameter=parameter, suite_parameter=suite_parameter,
                    name="new test name", expected="updated expectation")
        if suite_parameter == 1 and parameter == 10:
            raise Exception("On purpose")

    @test(retry=2, parameters=[10, 20], tags=["critical", "v1"],
          meta=meta(name="Retry 3", expected="Test must fail and be retried"))
    def retry4(self, parameter):
        assert parameter is not None
        Meta.update(parameter=parameter, name="new test name", expected="updated expectation")
        if parameter == 10:
            raise Exception("On purpose")

    @test(retry=2, tags=["critical", "v1"],
          meta=meta(name="Retry 3", expected="Test must fail and be retried"))
    def retry5(self, suite_parameter):
        assert suite_parameter is not None
        Meta.update(suite_parameter=suite_parameter, name="new test name", expected="updated expectation")
        if suite_parameter == 1:
            raise Exception("On purpose")

    @test(tags=["skip", "v2"])
    def skip(self):

        Meta.update(name="new test name", expected="updated expectation")
