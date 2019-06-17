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

    @test(retry=2, parameters=[10, 20], tags=["critical2", "v1"],
          meta=meta(name="No Retry", expected="Test must pass on 1st go, thus should not be retried"))
    def no_retry(self, parameter, suite_parameter):
        assert parameter is not None
        assert suite_parameter is not None
        Meta.update(self, parameter=parameter, suite_parameter=suite_parameter,
                    name="No Retry 1", expected="updated")
        Meta.get_meta(self, parameter=parameter, suite_parameter=suite_parameter)

    @test(retry=2, parameters=[10, 20], tags=["critical2", "v1"], parallalized_parameters=True,
          meta=meta(name="No Retry", expected="Test must pass on 1st go, thus should not be retried"))
    def no_retry2(self, parameter):
        assert parameter is not None
        Meta.update(self, parameter=parameter, name="No Retry 2", expected="updated")
        Meta.get_meta(self, parameter=parameter)

    @test(retry=2, tags=["critical2", "v1"],
          meta=meta(name="No Retry", expected="Test must pass on 1st go, thus should not be retried"))
    def no_retry3(self, suite_parameter):
        assert suite_parameter is not None
        Meta.update(self, suite_parameter=suite_parameter, name="No Retry 3", expected="updated")
        Meta.get_meta(self, suite_parameter=suite_parameter)

    @test(retry=2, tags=["critical2"])
    def retry(self):
        Meta.update(self, name="Retry", expected="Updated for Retry")
        Meta.get_meta(self)
        assert True is False, "Expected Assertion Error"

    @test(retry=2, tags=["trivial"])
    def retry2(self):
        Meta.update(self, name="new test name", expected="updated expectation")
        Meta.get_meta(self)
        assert True is False, "Expected Assertion Error 2"

    @test(retry=2, parameters=[10, 20], tags=["critical", "v2"],
          meta=meta(name="Retry 3", expected="Test must fail and be retried"))
    def retry3(self, parameter, suite_parameter):
        assert parameter is not None
        assert suite_parameter is not None
        Meta.update(self, parameter=parameter, suite_parameter=suite_parameter,
                    name="new test name", expected="updated expectation")
        Meta.get_meta(self, parameter=parameter, suite_parameter=suite_parameter)
        if suite_parameter == 1 and parameter == 10:
            raise Exception("On purpose")

    @test(retry=2, parameters=[10, 20], tags=["critical", "v2"],
          meta=meta(name="Retry 3", expected="Test must fail and be retried"))
    def retry4(self, parameter):
        assert parameter is not None
        Meta.update(self, parameter=parameter, name="new test name", expected="updated expectation")
        Meta.get_meta(self, parameter=parameter)
        if parameter == 10:
            raise Exception("On purpose")

    @test(retry=2, tags=["critical", "v2"],
          meta=meta(name="Retry 3", expected="Test must fail and be retried"))
    def retry5(self, suite_parameter):
        assert suite_parameter is not None
        Meta.update(self, suite_parameter=suite_parameter, name="new test name", expected="updated expectation")
        Meta.get_meta(self, suite_parameter=suite_parameter)
        if suite_parameter == 1:
            raise Exception("On purpose")

    @test(tags=["skip", "v2"])
    def skip(self):

        Meta.update(self, name="new test name", expected="updated expectation")
        Meta.get_meta(self)
