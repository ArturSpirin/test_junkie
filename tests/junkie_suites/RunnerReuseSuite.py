from test_junkie.decorators import Suite, test, GroupRules, beforeGroup, afterGroup

CALLS = []


@Suite()
class RunnerReuseSuite:

    @test()
    def test_a(self):
        CALLS.append("test_a")

    @test()
    def test_b(self):
        CALLS.append("test_b")


@GroupRules()
def runner_reuse_rules(rules):

    @beforeGroup([RunnerReuseSuite])
    def before_group():
        CALLS.append("beforeGroup")

    @afterGroup([RunnerReuseSuite])
    def after_group():
        CALLS.append("afterGroup")


FULL_RUN = ["beforeGroup", "test_a", "test_b", "afterGroup"]


def run(runner, **kwargs):
    """
    :return: LIST of what got called during runner.run(**kwargs)
    """
    del CALLS[:]
    runner.run(**kwargs)
    return list(CALLS)
