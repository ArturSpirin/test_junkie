
from test_junkie.runner import Runner
from tests.junkie_suites.AdvancedSuite import AdvancedSuite
from tests.junkie_suites.BasicSuite import BasicSuite


def order1():
    runner = Runner(suites=[AdvancedSuite])
    runner.run(
        features=["AdvancedSuite"],
        tag_config={
            "run_on_match_any": ["critical2"]
        }
    )


def order2():
    runner = Runner(suites=[AdvancedSuite, BasicSuite])
    runner.run(
        features=["AdvancedSuite"],
        tag_config={
            "run_on_match_any": ["critical2"]
        }
    )


def order_all():
    funcs = [order1, order2]
    for func in funcs:
        try:
            func()
        except ValueError:
            print('TEST')
            break


order_all()
