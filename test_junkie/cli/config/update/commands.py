import click

from test_junkie.constants import CliConstants
from test_junkie.cli.utils import PythonLiteralOption
from test_junkie.cli.config.Config import Config
from rich import print

config = Config(CliConstants.TJ_CONFIG_NAME)


@click.command()
@click.help_option('-h', '--help')
@click.option('-s', "--sources", cls=PythonLiteralOption, type=list,
              help="Paths to DIRECTORY or FILE where you have your tests."
                   "Test Junkie will traverse this source(s) looking for test suites.")
@click.option('-T', "--test_multithreading_limit", type=int,
              help="Test level multi threading allows to run multiple tests concurrently.")
@click.option('-S', "--suite_multithreading_limit", type=int,
              help="Suite level multi threading allows to run multiple suites concurrently.")
@click.option('-t', "--tests", cls=PythonLiteralOption, type=list,
              help="Test Junkie can run specific tests. Provide the names of the tests that you want to execute/audit.")
@click.option('-f', "--features", cls=PythonLiteralOption, type=list,
              help="Test suites can be defined with a feature that they are testing. "
                   "Use features to narrow down execution/audit of test suites only to those that match this filter. "
                   "Learn more @ https://www.test-junkie.com/documentation/#features")
@click.option('-c', "--components", cls=PythonLiteralOption, type=list,
              help="Tests can be defined with a component that they are testing. "
                   "Use components to narrow down execution/audit of tests only to those that match this filter. "
                   "Learn more @ https://www.test-junkie.com/documentation/#components")
@click.option('-o', "--owners", cls=PythonLiteralOption, type=list,
              help="Tests & test suites can be defined with an assignee. "
                   "Use owners to narrow down execution/audit of tests only to those that match this filter. "
                   "Learn more @ https://www.test-junkie.com/documentation/#assignees")
@click.option('-m', "--monitor_resources", type=bool,
              help="Test Junkie can track resource usage for CPU & Memory as it runs tests")
@click.option('-l', "--run_on_match_all", cls=PythonLiteralOption, type=list,
              help="Test Junkie will RUN tests that match ALL of the tags. "
                   "Read more about it: https://www.test-junkie.com/documentation/#tags")
@click.option('-k', "--run_on_match_any", cls=PythonLiteralOption, type=list,
              help="Test Junkie will RUN tests that match ANY of the tags. "
                   "Read more about it: https://www.test-junkie.com/documentation/#tags")
@click.option('-j', "--skip_on_match_all", cls=PythonLiteralOption, type=list,
              help="Test Junkie will SKIP tests that match ALL of the tags. "
                   "Read more about it: https://www.test-junkie.com/documentation/#tags")
@click.option('-g', "--skip_on_match_any", cls=PythonLiteralOption, type=list,
              help="Test Junkie will SKIP tests that match ANY of the tags. "
                   "Read more about it: https://www.test-junkie.com/documentation/#tags")
@click.option("--html_report", type=str,
              help="Path to FILE. This will enable HTML report generation and when ready, "
                   "the report will be saved to the specified file")
@click.option("--xml_report", type=str,
              help="Path to FILE. This will enable XML report generation and when ready, "
                   "the report will be saved to the specified file")
def update(sources, test_multithreading_limit, suite_multithreading_limit, tests, features, components, owners,
           monitor_resources, run_on_match_all, run_on_match_any, skip_on_match_all, skip_on_match_any, html_report,
           xml_report):
    """Update configuration settings for individual properties"""
    for option, value in locals().items():
        if value is not None:
            if isinstance(value, list):
                print(f"[[[bold green]OK[/bold green]]] {option}=[{value}]")
            else:
                print(f"[[[bold green]OK[/bold green]]] {option}={value}")
            config.set_value(option, value)
