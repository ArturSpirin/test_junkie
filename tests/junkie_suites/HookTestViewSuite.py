from test_junkie.decorators import Suite, test, beforeTest, afterTest
from test_junkie.meta import Meta
from test_junkie.objects import TestObject

SEEN = []


@Suite(parameters=["admin", "viewer"])
class HookTestViewSuite:

    @beforeTest()
    def before(self, test, suite_parameter):
        SEEN.append(("before", test.get_function_name(), list(test.get_tags()), suite_parameter,
                     test.accepts_suite_parameters()))
        # every way a hook might try to change the test: none of it may reach the live object
        test.get_tags().append("mutated")
        test.get_kwargs()["tags"].append("mutated")
        test.get_meta()["name"] = "mutated"
        test.custom_flag = True
        SEEN.append(("local", test.custom_flag))
        SEEN.append(("isinstance", isinstance(test, TestObject)))

    @afterTest()
    def after(self, test):
        SEEN.append(("after", test.get_function_name(), test.suite.get_class_name()))

    @test(tags=["ui"], meta={"name": "original"})
    def per_account(self, suite_parameter):
        Meta.update(self, suite_parameter=suite_parameter, recorded=suite_parameter)

    @test(tags=["api"])
    def once(self):
        pass


@Suite()
class HookTestViewMutatorSuite:

    @beforeTest()
    def before(self, test):
        test.suite.update_test_objects([])  # would empty the live suite: must fail this hook only

    @test()
    def guarded(self):
        pass


@Suite()
class HookTestViewThreadedSuite:
    # hooks copy the test while sibling threads write meta into the same test

    @beforeTest()
    def before(self, test):
        test.get_kwargs()
        test.get_meta()

    @afterTest()
    def after(self, test):
        test.metrics.get_metrics()

    @test(parameters=list(range(40)), parallelized_parameters=True)
    def busy(self, parameter):
        for i in range(25):
            Meta.update(self, parameter=parameter, **{"k{}".format(i): i})


@Suite()
class HookWithoutTestArgSuite:

    CALLS = []

    @beforeTest()
    def before(self):
        HookWithoutTestArgSuite.CALLS.append("before")

    @test()
    def plain(self):
        pass
