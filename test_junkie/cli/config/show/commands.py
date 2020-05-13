import click

from test_junkie.constants import CliConstants, Undefined
from test_junkie.cli.config.Config import Config
from rich import print

config = Config(CliConstants.TJ_CONFIG_NAME)


@click.command()
@click.help_option('-h', '--help')
@click.option('-s', "--sources", is_flag=True)
@click.option('-T', "--test_multithreading_limit", is_flag=True)
@click.option('-S', "--suite_multithreading_limit", is_flag=True)
@click.option('-t', "--tests", is_flag=True)
@click.option('-f', "--features", is_flag=True)
@click.option('-c', "--components", is_flag=True)
@click.option('-o', "--owners", is_flag=True)
@click.option('-m', "--monitor_resources", is_flag=True)
@click.option('-l', "--run_on_match_all", is_flag=True)
@click.option('-k', "--run_on_match_any", is_flag=True)
@click.option('-j', "--skip_on_match_all", is_flag=True)
@click.option('-g', "--skip_on_match_any", is_flag=True)
@click.option("--html_report", is_flag=True)
@click.option("--xml_report", is_flag=True)
def show(sources, test_multithreading_limit, suite_multithreading_limit, tests, features, components, owners,
         monitor_resources, run_on_match_all, run_on_match_any, skip_on_match_all, skip_on_match_any, html_report,
         xml_report):
    """Display current configuration for Test-Junkie"""
    specific = True in list(locals().values())
    if not specific:
        print("\nSource: [bold]'{path}'[/bold]\n".format(path=config.path))
        with open(config.path, "r") as cfg:
            print(cfg.read().replace("[", "[[").replace("]", "]]").replace("[[runtime]]", ""))
    else:
        print("\nSource: [bold]'{path}'[/bold]\n".format(path=config.path))
        for option, value in locals().items():
            if value is True:
                value = config.get_value(option)
                if value != Undefined:
                    if isinstance(value, list):
                        print(f"{option}=[{value}]")
                    else:
                        print(f"{option}={value}")
