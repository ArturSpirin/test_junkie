import click
from test_junkie.cli.config.show import commands as show_command
from test_junkie.cli.config.restore import commands as restore_command
from test_junkie.cli.config.update import commands as update_command


@click.group()
@click.help_option('-h', '--help')
def config():
    """Configure Test Junkie"""
    pass


config.add_command(show_command.show)
config.add_command(restore_command.restore)
config.add_command(update_command.update)
