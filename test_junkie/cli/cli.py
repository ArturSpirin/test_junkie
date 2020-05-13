import click
from test_junkie.cli.run import commands as run_commands
from test_junkie.cli.audit import commands as audit_commands
from test_junkie.cli.config import commands as config_commands
from test_junkie.cli.version import commands as version_commands
from test_junkie.cli.hq import commands as hq_commands


@click.group()
@click.help_option('-h', '--help')
def entry_point():
    pass


entry_point.add_command(run_commands.run)
entry_point.add_command(audit_commands.audit)
entry_point.add_command(config_commands.config)
entry_point.add_command(version_commands.version)
entry_point.add_command(hq_commands.hq)
entry_point()
