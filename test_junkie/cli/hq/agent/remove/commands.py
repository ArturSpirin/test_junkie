import click


from test_junkie.cli.hq.agent.agent import Agent

_agent = Agent()


@click.command()
@click.help_option('-h', '--help')
@click.argument("agent")
def remove(agent):
    """Remove an existing agent."""
    _agent.remove(agent)
