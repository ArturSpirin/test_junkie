import click
from test_junkie.cli.hq.agent.add import commands as add_commands
from test_junkie.cli.hq.agent.list import commands as list_commands
from test_junkie.cli.hq.agent.remove import commands as remove_commands
from test_junkie.cli.hq.agent.update import commands as update_commands


@click.group(chain=True)
@click.help_option('-h', '--help')
def agent():
    """Control Test Junkie HQ Agents."""
    pass


agent.add_command(add_commands.add)
agent.add_command(update_commands.update)
agent.add_command(remove_commands.remove)
agent.add_command(list_commands.list)
