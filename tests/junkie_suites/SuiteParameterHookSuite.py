from test_junkie.decorators import Suite, test, beforeTest, afterTest
from test_junkie.meta import Meta

CALLS = []
FAILING = set()  # suite parameters under which plain fails


@Suite(parameters=["a", "b"], every_test_per_parameter=True)
class EveryTestPerParameterSuite:
    # plain and with_params don't declare suite_parameter: with the flag on they still run once per suite parameter

    @beforeTest()
    def before(self, suite_parameter):
        CALLS.append(("before", suite_parameter))
        EveryTestPerParameterSuite.running = suite_parameter

    @afterTest()
    def after(self, suite_parameter):
        CALLS.append(("after", suite_parameter))

    @test()
    def plain(self):
        CALLS.append(("plain", EveryTestPerParameterSuite.running))
        Meta.update(seen=EveryTestPerParameterSuite.running)
        assert EveryTestPerParameterSuite.running not in FAILING

    @test(parameters=[1, 2])
    def with_params(self, parameter):
        CALLS.append(("with_params", EveryTestPerParameterSuite.running, parameter))


@Suite(parameters=["a", "b"])
class HookOnlySuite:
    # same hooks without the flag: plain runs once and its hooks get None, as before

    @beforeTest()
    def before(self, suite_parameter):
        CALLS.append(("before", suite_parameter))

    @afterTest()
    def after(self, suite_parameter):
        CALLS.append(("after", suite_parameter))

    @test()
    def plain(self):
        CALLS.append(("plain", None))


@Suite(every_test_per_parameter=True)
class FlagWithoutParametersSuite:
    # no suite parameters: the flag changes nothing

    @beforeTest()
    def before(self, suite_parameter):
        CALLS.append(("before", suite_parameter))

    @test()
    def plain(self):
        CALLS.append(("plain", None))


def run(suite, failing=(), **kwargs):
    """
    :return: (CALLS, Aggregator, the suite's SuiteObject)
    """
    from test_junkie.builder import Builder
    from test_junkie.runner import Runner
    del CALLS[:]
    FAILING.clear()
    FAILING.update(failing)
    aggregator = Runner([suite], quiet=True).run(**kwargs)
    FAILING.clear()
    return list(CALLS), aggregator, Builder.get_execution_roster().get(suite)


def live(suite_object, name):
    return {t.get_function_name(): t for t in suite_object.get_test_objects()}[name]
