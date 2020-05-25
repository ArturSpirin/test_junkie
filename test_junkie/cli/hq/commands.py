import click
from test_junkie.cli.hq.agent import commands as agent_commands
from test_junkie.cli.hq.connect import commands as connect_commands


@click.group()
@click.help_option('-h', '--help')
def hq():
    """Integrate with Test Junkie HQ."""
    pass


hq.add_command(agent_commands.agent)
hq.add_command(connect_commands.add)
hq.add_command(connect_commands.list)
hq.add_command(connect_commands.remove)
hq.add_command(connect_commands.status)
hq.add_command(connect_commands.start)
hq.add_command(connect_commands.stop)
