from test_junkie.decorators import Suite, test
from tests.junkie_suites.TestListener import TestListener


@Suite(retry=2,
       listener=TestListener,
       parameters=[1, 2],
       parallelized=False,
       feature="API")
class AuthApiSuite:

    @test(component="Auth", tags=["api", "auth", "basic_auth"], owner="Victor")
    def authenticate_via_basic_auth_api(self):
        pass

    @test(component="Auth", tags=["api", "auth", "two_factor"], owner="Victor")
    def authenticate_via_two_factor_api(self):
        pass

    @test(component="Auth", tags=["api", "auth", "sso"], owner="Mike")
    def authenticate_via_sso(self):
        pass

    @test(component="Auth", tags=["api", "auth", "sso"], owner="Mike")
    def sso_hit_negative_auth_limit(self):
        pass

    @test(component="Auth", tags=["api", "auth", "basic_auth"], owner="Victor")
    def auth_hit_negative_auth_limit(self):
        pass

    @test(component="Auth", tags=["api", "auth", "two_factor"], owner="Victor")
    def two_factor_hit_negative_auth_limit(self):
        pass


@Suite(retry=2,
       listener=TestListener,
       meta={"name": "Suite B", "known_bugs": []},
       parameters=[1, 2], priority=1, feature="Store",
       owner="George")
class ShoppingCartSuite:

    @test(priority=1,
          component="Shopping Cart",
          tags=["ui", "cart", "positive_flow"])
    def add_to_cart(self):
        pass

    @test(priority=1,
          component="Shopping Cart",
          tags=["ui", "cart", "positive_flow"])
    def remove_from_cart(self):
        pass

    @test(priority=1,
          component="Shopping Cart",
          tags=["ui", "cart", "positive_flow"])
    def increase_quantity(self):
        pass

    @test(priority=1,
          component="Shopping Cart",
          tags=["ui", "cart", "positive_flow"])
    def decrease_quantity(self):
        pass

    @test(priority=1,
          component="Shopping Cart",
          tags=["ui", "cart", "positive_flow"])
    def save_for_later(self):
        pass


@Suite(retry=2,
       listener=TestListener,
       priority=2, feature="Store", owner="Mike")
class NewProductsSuite:

    @test(component="Admin", tags=["store_management"])
    def add_new_product(self):
        pass

    @test(component="Admin", tags=["store_management"])
    def remove_product(self):
        pass

    @test(component="Admin", tags=["store_management"])
    def publish_product(self):
        pass

    @test(component="Admin", tags=["store_management"])
    def edit_product(self):
        pass

    @test(component="Admin", tags=["store_management"])
    def archive_product(self):
        pass
