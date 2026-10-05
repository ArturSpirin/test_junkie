from test_junkie.constants import TestOrder
from test_junkie.decorators import Suite, test

# Each list is appended to in test-execution order, giving us a ground-truth sequence to assert against.
alpha_order = []
priority_asc_order = []
priority_desc_order = []
random_order = []
default_order = []
invalid_value_order = []


@Suite(order=TestOrder.ALPHABETICAL)
class AlphaSuite:
    """Tests declared in non-alphabetical order to prove sorting."""

    @test()
    def test_zebra(self): alpha_order.append("test_zebra")

    @test()
    def test_apple(self): alpha_order.append("test_apple")

    @test()
    def test_mango(self): alpha_order.append("test_mango")

    @test()
    def test_banana(self): alpha_order.append("test_banana")


@Suite(order=TestOrder.PRIORITY_ASC)
class PriorityAscSuite:
    """Tests declared in a scrambled priority order to prove ascending sort."""

    @test(priority=3)
    def test_low(self): priority_asc_order.append("test_low")

    @test(priority=1)
    def test_high(self): priority_asc_order.append("test_high")

    @test(priority=2)
    def test_mid(self): priority_asc_order.append("test_mid")

    @test()
    def test_unprioritized(self): priority_asc_order.append("test_unprioritized")


@Suite(order=TestOrder.PRIORITY_DESC)
class PriorityDescSuite:
    """Same layout as PriorityAscSuite — proves descending is the exact mirror."""

    @test(priority=3)
    def test_low(self): priority_desc_order.append("test_low")

    @test(priority=1)
    def test_high(self): priority_desc_order.append("test_high")

    @test(priority=2)
    def test_mid(self): priority_desc_order.append("test_mid")

    @test()
    def test_unprioritized(self): priority_desc_order.append("test_unprioritized")


@Suite(order=TestOrder.RANDOM)
class RandomSuite:
    """Five tests so a false-positive accidental match is 1/120 without mocking."""

    @test()
    def test_a(self): random_order.append("test_a")

    @test()
    def test_b(self): random_order.append("test_b")

    @test()
    def test_c(self): random_order.append("test_c")

    @test()
    def test_d(self): random_order.append("test_d")

    @test()
    def test_e(self): random_order.append("test_e")


@Suite()
class DefaultSuite:
    """No order= kwarg — should behave identically to PRIORITY_ASC (backward compat)."""

    @test(priority=3)
    def test_low(self): default_order.append("test_low")

    @test(priority=1)
    def test_high(self): default_order.append("test_high")

    @test(priority=2)
    def test_mid(self): default_order.append("test_mid")

    @test()
    def test_unprioritized(self): default_order.append("test_unprioritized")


@Suite(order="banana")
class InvalidValueSuite:
    """order= is a valid string type but not a recognised TestOrder constant.
    BadParameters must be raised at run time (inside __prioritize), not at decoration time."""

    @test()
    def test_x(self): invalid_value_order.append("test_x")
