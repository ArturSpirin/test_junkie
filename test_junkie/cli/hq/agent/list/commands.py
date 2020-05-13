import click

from test_junkie.cli.hq.agent.agent import Agent

_agent = Agent()


@click.command()
@click.help_option('-h', '--help')
@click.option('--hq', help="List agent for specific HQ")
def list(hq):
    """List all existing agents."""
    _agent.ls(hq)
