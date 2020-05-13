import click

from test_junkie.cli.hq.hq import HQ

_hq = HQ()


@click.command()
@click.help_option('-h', '--help')
@click.option('-n', '--name', help="Give a custom name to this server", default=None, type=str)
@click.argument('host')
def add(host, name):
    """Add a server."""
    if not host.startswith("http"):
        print("Host must include protocol aka https://example.com:80")
        exit(1)
    _hq.add(host, name)


@click.command()
@click.help_option('-h', '--help')
def list():
    """List all connected servers."""
    _hq.ls()


@click.command()
@click.help_option('-h', '--help')
@click.argument('hq')
def remove(hq):
    """Remove a connected server."""
    _hq.remove(hq)


@click.command()
@click.help_option('-h', '--help')
def status():
    """Current status regarding HQ & Agents."""
    print("Status!")
