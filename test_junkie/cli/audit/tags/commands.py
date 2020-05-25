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
@click.option('-x', "--suites", cls=PythonLiteralOption, type=list, default=None,
              help="Test Junkie will only run suites provided, given that they are found in the SOURCES.")
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
@click.option('-l', "--tags", cls=PythonLiteralOption, type=list, default=Undefined,
              help="Test Junkie will audit tests that match those tags.")
@click.option("--by-component", is_flag=True,
              help="Present aggregated data broken down by components")
@click.option("--by-features", is_flag=True,
              help="Present aggregated data broken down by features")
@click.option("--no-rules", is_flag=True,
              help="Aggregate data only for suites that do not have any rules set")
@click.option("--no-listeners", is_flag=True,
              help="Aggregate data only for suites that do not have any event listeners set")
@click.option("--no-suite-retries", is_flag=True,
              help="Aggregate data only for suites that do not have retries set")
@click.option("--no-test-retries", is_flag=True,
              help="Aggregate data only for tests that do not have retries set")
@click.option("--no-suite-meta", is_flag=True,
              help="Aggregate data only for suites that do not have any meta information set")
@click.option("--no-test-meta", is_flag=True,
              help="Aggregate data only for tests that do not have any meta information set")
@click.option("--no-owners", is_flag=True,
              help="Aggregate data only for tests that do not have any owners defined")
@click.option("--no-features", is_flag=True,
              help="Aggregate data only for suites that do not have features defined")
@click.option("--no-components", is_flag=True,
              help="Aggregate data only for tests that do not have any components defined")
@click.option("--no-tags", is_flag=True,
              help="Aggregate data only for tests that do not have tags defined")
@click.option("--no-guess-root", is_flag=True,
              help="By default if there is an import error, Test Junkie will attempt to add your project to the PATH"
                   " so Python can find your packages. Generally, its recommended to do this yourself so you have"
                   " an option to disable this feature.")
@click.option("-v", "--verbose", is_flag=True,
              help="Enables Test Junkie's logs for debugging purposes")
def tags(sources, suites, features, components, owners, tags, no_guess_root, verbose, no_features, no_owners,
         no_components, no_tags, by_component, by_features, no_rules, no_listeners, no_suite_retries,
         no_test_retries, no_suite_meta, no_test_meta):
    """Pivot test information from tag's perspective"""
    if verbose:
        from test_junkie.debugger import LogJunkie
        LogJunkie.enable_logging(10)

    from test_junkie.cli.run.cli_runner import CliRunner
    from test_junkie.cli.audit.cli_audit import CliAudit
    try:
        tj = CliRunner(sources=sources, ignore=[".git"], suites=suites, no_guess_root=no_guess_root)
        tj.scan()
        aggregator = CliAudit(suites=tj.suites, args=locals())
        aggregator.aggregate()
        aggregator.print_results(command="tags")
    except BadCliParameters as error:
        print("[[[bold red]ERROR[/bold red]]] [bold red]{error}[/bold red]".format(error=error))
