import click

from test_junkie.cli.hq.agent.agent import Agent

_agent = Agent()


@click.command()
@click.help_option('-h', '--help')
@click.option('--name', help="Name your agent")
@click.argument('hq')
@click.argument('project')
def add(hq, project, name):
    """Add an agent to a repository."""
    _agent.add(hq, project, name)
