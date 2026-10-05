from unittest.mock import patch

from test_junkie.builder import Builder
from test_junkie.decorators import Suite, test
from test_junkie.errors import BadParameters
from test_junkie.runner import Runner

from tests.junkie_suites.ordering.OrderingSuites import (
    AlphaSuite, alpha_order,
    PriorityAscSuite, priority_asc_order,
    PriorityDescSuite, priority_desc_order,
    RandomSuite, random_order,
    DefaultSuite, default_order,
    InvalidValueSuite,
)


@Suite()
class OrderingTestSuite:

    @test()
    def alpha_sequence(self):
        alpha_order.clear()
        Runner([AlphaSuite]).run()
        assert alpha_order == ["test_apple", "test_banana", "test_mango", "test_zebra"]

    @test()
    def alpha_all_tests_execute(self):
        alpha_order.clear()
        Runner([AlphaSuite]).run()
        assert set(alpha_order) == {"test_apple", "test_banana", "test_mango", "test_zebra"}

    @test()
    def alpha_no_duplicates(self):
        alpha_order.clear()
        Runner([AlphaSuite]).run()
        assert len(alpha_order) == len(set(alpha_order))

    @test()
    def priority_asc_sequence(self):
        priority_asc_order.clear()
        Runner([PriorityAscSuite]).run()
        assert priority_asc_order == ["test_high", "test_mid", "test_low", "test_unprioritized"]

    @test()
    def priority_asc_all_tests_execute(self):
        priority_asc_order.clear()
        Runner([PriorityAscSuite]).run()
        assert set(priority_asc_order) == {"test_high", "test_mid", "test_low", "test_unprioritized"}

    @test()
    def priority_asc_unprioritized_last(self):
        priority_asc_order.clear()
        Runner([PriorityAscSuite]).run()
        assert priority_asc_order[-1] == "test_unprioritized"

    @test()
    def priority_desc_sequence(self):
        priority_desc_order.clear()
        Runner([PriorityDescSuite]).run()
        assert priority_desc_order == ["test_low", "test_mid", "test_high", "test_unprioritized"]

    @test()
    def priority_desc_all_tests_execute(self):
        priority_desc_order.clear()
        Runner([PriorityDescSuite]).run()
        assert set(priority_desc_order) == {"test_high", "test_mid", "test_low", "test_unprioritized"}

    @test()
    def priority_desc_unprioritized_last(self):
        priority_desc_order.clear()
        Runner([PriorityDescSuite]).run()
        assert priority_desc_order[-1] == "test_unprioritized"

    @test()
    def asc_and_desc_are_mirrors(self):
        priority_asc_order.clear()
        priority_desc_order.clear()
        Runner([PriorityAscSuite]).run()
        Runner([PriorityDescSuite]).run()
        asc_pri = [t for t in priority_asc_order if t != "test_unprioritized"]
        desc_pri = [t for t in priority_desc_order if t != "test_unprioritized"]
        assert asc_pri == list(reversed(desc_pri))

    @test()
    def random_all_tests_execute(self):
        random_order.clear()
        Runner([RandomSuite]).run()
        assert set(random_order) == {"test_a", "test_b", "test_c", "test_d", "test_e"}

    @test()
    def random_no_duplicates(self):
        random_order.clear()
        Runner([RandomSuite]).run()
        assert len(random_order) == len(set(random_order))

    @test()
    def random_invokes_shuffle(self):
        random_order.clear()
        with patch("test_junkie.runner.random") as mock_random:
            mock_random.shuffle.side_effect = lambda lst: None
            Runner([RandomSuite]).run()
        mock_random.shuffle.assert_called_once()

    @test()
    def random_respects_shuffle_result(self):
        random_order.clear()
        captured = []

        def capture_and_reverse(lst):
            captured.extend(lst)
            lst.reverse()

        with patch("test_junkie.runner.random") as mock_random:
            mock_random.shuffle.side_effect = capture_and_reverse
            Runner([RandomSuite]).run()

        expected = [t.get_function_name() for t in reversed(captured)]
        assert random_order == expected

    @test()
    def default_order_matches_priority_asc(self):
        default_order.clear()
        Runner([DefaultSuite]).run()
        assert default_order == ["test_high", "test_mid", "test_low", "test_unprioritized"]

    @test()
    def default_all_tests_execute(self):
        default_order.clear()
        Runner([DefaultSuite]).run()
        assert set(default_order) == {"test_high", "test_mid", "test_low", "test_unprioritized"}

    @test()
    def default_unprioritized_last(self):
        default_order.clear()
        Runner([DefaultSuite]).run()
        assert default_order[-1] == "test_unprioritized"

    @test()
    def invalid_order_value_raises_bad_parameters(self):
        raised = False
        try:
            Runner([InvalidValueSuite])
        except BadParameters as e:
            raised = True
            assert "banana" in str(e)
            assert "order" in str(e).lower()
        assert raised

    @test()
    def invalid_order_type_raises_at_decoration(self):
        from test_junkie.decorators import Suite as TjSuite, test as tj_test
        raised = False
        try:
            @TjSuite(order=42)
            class _BadTypeSuite:
                @tj_test()
                def test_x(self): pass
        except BadParameters:
            raised = True
        finally:
            Builder._Builder__set_current_suite_object_defaults()
        assert raised
