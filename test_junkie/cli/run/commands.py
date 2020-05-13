import click

from test_junkie.constants import Undefined
from test_junkie.errors import BadCliParameters
from test_junkie.cli.utils import PythonLiteralOption
from rich import print


@click.command()
@click.help_option('-h', '--help')
@click.option('-s', "--sources", cls=PythonLiteralOption, type=list, default=Undefined,
              help="Paths to DIRECTORY or FILE where you have your tests."
                   "Test Junkie will traverse this source(s) looking for test suites.")
@click.option('-T', "--test-multithreading-limit", default=Undefined,
              help="Test level multi threading allows to run multiple tests concurrently.")
@click.option('-S', "--suite-multithreading-limit", default=Undefined,
              help="Suite level multi threading allows to run multiple suites concurrently.")
@click.option('-x', "--suites", cls=PythonLiteralOption, type=list, default=None,
              help="Test Junkie will only run suites provided, given that they are found in the SOURCES.")
@click.option('-t', "--tests", cls=PythonLiteralOption, type=list, default=Undefined,
              help="Test Junkie can run specific tests. Provide the names of the tests that you want to execute/audit.")
@click.option('-f', "--features", cls=PythonLiteralOption, type=list, default=Undefined,
              help="Test suites can be defined with a feature that they are testing. "
                   "Use features to narrow down execution/audit of test suites only to those that match this filter. "
                   "Learn more @ https://www.test-junkie.com/documentation/#features")
@click.option('-c', "--components", cls=PythonLiteralOption, type=list, default=Undefined,
              help="Tests can be defined with a component that they are testing. "
                   "Use components to narrow down execution/audit of tests only to those that match this filter. "
                   "Learn more @ https://www.test-junkie.com/documentation/#components")
@click.option('-o', "--owners", cls=PythonLiteralOption, type=list, default=Undefined,
              help="Tests & test suites can be defined with an assignee. "
                   "Use owners to narrow down execution/audit of tests only to those that match this filter. "
                   "Learn more @ https://www.test-junkie.com/documentation/#assignees")
@click.option('-m', "--monitor-resources", is_flag=True,
              help="Test Junkie can track resource usage for CPU & Memory as it runs tests")
@click.option('-l', "--run-on-match-all", cls=PythonLiteralOption, type=list, default=Undefined,
              help="Test Junkie will RUN tests that match ALL of the tags. "
                   "Read more about it: https://www.test-junkie.com/documentation/#tags")
@click.option('-k', "--run-on-match-any", cls=PythonLiteralOption, type=list, default=Undefined,
              help="Test Junkie will RUN tests that match ANY of the tags. "
                   "Read more about it: https://www.test-junkie.com/documentation/#tags")
@click.option('-j', "--skip-on-match-all", cls=PythonLiteralOption, type=list, default=Undefined,
              help="Test Junkie will SKIP tests that match ALL of the tags. "
                   "Read more about it: https://www.test-junkie.com/documentation/#tags")
@click.option('-g', "--skip-on-match-any", cls=PythonLiteralOption, type=list, default=Undefined,
              help="Test Junkie will SKIP tests that match ANY of the tags. "
                   "Read more about it: https://www.test-junkie.com/documentation/#tags")
@click.option('-q', "--no-quiet", is_flag=True,
              help="Suppress all standard output from tests")
@click.option('-v', "--verbose", is_flag=True,
              help="Enables Test Junkie's logs for debugging purposes")
@click.option("--html_report", default=Undefined,
              help="Path to FILE. This will enable HTML report generation and when ready, "
                   "the report will be saved to the specified file")
@click.option("--xml_report", default=Undefined,
              help="Path to FILE. This will enable XML report generation and when ready, "
                   "the report will be saved to the specified file")
@click.option("--no-guess-root", is_flag=True,
              help="Test Junkie can track resource usage for CPU & Memory as it runs tests")
@click.option("--rich-traceback", is_flag=True,
              help="Enables more visual tracebacks with syntax highlighting")
@click.option("--code-cov", is_flag=True,
              help="Measure code coverage")
@click.option("--cov-rcfile", default=Undefined,
              help="Path to configuration FILE for coverage.py "
                   "See https://coverage.readthedocs.io/en/v4.5.x/config.html")
@click.option("--config", default=Undefined,
              help="Provide your own config FILE with settings for test execution.")
def run(sources, test_multithreading_limit, suite_multithreading_limit, suites, tests, features, components, owners,
        monitor_resources, run_on_match_all, run_on_match_any, skip_on_match_all, skip_on_match_any, html_report,
        xml_report, no_quiet, verbose, no_guess_root, code_cov, cov_rcfile, config, rich_traceback):
    """Run tests in any directory (recursive)"""
    if rich_traceback:
        from rich.traceback import install
        install()
    if verbose:
        from test_junkie.debugger import LogJunkie
        LogJunkie.enable_logging(10)

    from test_junkie.cli.run.cli_runner import CliRunner
    try:
        tj = CliRunner(sources=sources, ignore=[".git"], suites=suites,
                       code_cov=code_cov, cov_rcfile=cov_rcfile, no_guess_root=no_guess_root,
                       config=config)
        tj.scan()
    except BadCliParameters as error:
        print("[[[bold red]ERROR[/bold red]]] [bold red]{error}[/bold red]")
        return
    tj.run_suites(**locals())
