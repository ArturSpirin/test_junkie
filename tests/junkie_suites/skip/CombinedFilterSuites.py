"""
Two suites with different feature/owner/component/tag combinations, and pairs of Runner filters with the exact
tests each pair must run. Filters combine with AND - every filter narrows the same pool (see the "Running tests"
docs). Shared by the pytest and TJ test paths.
"""
from test_junkie.decorators import Suite, test

RAN = []


@Suite(feature="Login", owner="alice")
class CombinedFilterLoginSuite:

    @test(component="auth", tags=["smoke"])
    def auth_smoke(self):
        RAN.append("Login.auth_smoke")

    @test(component="auth", tags=["slow"])
    def auth_slow(self):
        RAN.append("Login.auth_slow")

    @test(component="ui", tags=["smoke"])
    def ui_smoke(self):
        RAN.append("Login.ui_smoke")


@Suite(feature="Cart", owner="bob")
class CombinedFilterCartSuite:

    @test(component="auth", tags=["smoke"])
    def cart_auth_smoke(self):
        RAN.append("Cart.cart_auth_smoke")

    @test(component="ui", tags=["slow"])
    def cart_ui_slow(self):
        RAN.append("Cart.cart_ui_slow")


CASES = [
    (dict(components=["auth"], tests=["ui_smoke"]), []),
    (dict(components=["auth"], tag_config={"run_on_match_any": ["smoke"]}),
     ["Cart.cart_auth_smoke", "Login.auth_smoke"]),
    (dict(features=["Login"], components=["ui"]), ["Login.ui_smoke"]),
    (dict(owners=["bob"], tag_config={"run_on_match_any": ["smoke"]}), ["Cart.cart_auth_smoke"]),
    (dict(tag_config={"run_on_match_any": ["smoke"]}, tests=["auth_slow"]), []),
    (dict(tag_config={"run_on_match_any": ["slow"], "run_on_match_all": ["slow"]}),
     ["Cart.cart_ui_slow", "Login.auth_slow"]),
    (dict(features=["Cart"], tests=["auth_smoke"]), []),
]


def run(**filters):
    """
    :return: sorted LIST of the tests that ran with these Runner.run() filters
    """
    from test_junkie.runner import Runner
    del RAN[:]
    Runner([CombinedFilterLoginSuite, CombinedFilterCartSuite], quiet=True).run(**filters)
    return sorted(RAN)
