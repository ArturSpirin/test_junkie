import click
from test_junkie.cli.audit.suites import commands as suites_command
from test_junkie.cli.audit.features import commands as features_command
from test_junkie.cli.audit.components import commands as components_command
from test_junkie.cli.audit.tags import commands as tags_command
from test_junkie.cli.audit.owners import commands as owners_command

@click.group()
@click.help_option('-h', '--help')
def audit():
    """Audit your tests in any directory (recursive)"""
    pass


audit.add_command(suites_command.suites)
audit.add_command(features_command.features)
audit.add_command(components_command.components)
audit.add_command(tags_command.tags)
audit.add_command(owners_command.owners)
