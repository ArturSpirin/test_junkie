from test_junkie.decorators import Suite, test, beforeClass, afterClass

CALLS = []
FLAKY_ONCE = []


@Suite(retry=2, parameters=["env_a", "env_b", "env_c"])
class RetrySetupTeardownSuite:
    """
    test fails once, only for env_b - so the retry pass must set up and tear down env_b again and nothing else
    """

    @beforeClass()
    def before_class(self, suite_parameter):
        CALLS.append("beforeClass:" + suite_parameter)

    @afterClass()
    def after_class(self, suite_parameter):
        CALLS.append("afterClass:" + suite_parameter)

    @test()
    def flaky_on_env_b(self, suite_parameter):
        CALLS.append("test:" + suite_parameter)
        if suite_parameter == "env_b" and not FLAKY_ONCE:
            FLAKY_ONCE.append(True)
            raise AssertionError("flaky once on env_b")


# first pass: every env once; retry pass: only env_b, set up and torn down exactly once more
EXPECTED_CALLS = ["beforeClass:env_a", "test:env_a", "afterClass:env_a",
                  "beforeClass:env_b", "test:env_b", "afterClass:env_b",
                  "beforeClass:env_c", "test:env_c", "afterClass:env_c",
                  "beforeClass:env_b", "test:env_b", "afterClass:env_b"]


def run():
    from test_junkie.runner import Runner
    del CALLS[:]
    del FLAKY_ONCE[:]
    Runner([RetrySetupTeardownSuite], quiet=True).run()
    return list(CALLS)
