import click


@click.command()
@click.help_option('-h', '--help')
@click.argument("agent")
def update(agent):
    """Update configuration of an existing agent."""
    print(f"Lets update {agent}!")
