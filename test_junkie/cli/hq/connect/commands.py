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
@click.option('-t', "--display_tokens",  is_flag=True, help="Will also display which token is being for communicating.")
@click.help_option('-h', '--help')
def list(display_tokens):
    """List all connected servers."""
    _hq.ls(display_tokens)


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
    if _hq.status():
        from test_junkie.cli.hq.agent.agent import Agent
        Agent().ls(None)


@click.command()
@click.option('-d', "--detached", is_flag=True,  help="Activates process in the background.")
@click.help_option('-h', '--help')
def start(detached):
    """Activates all the agents on this machine."""
    import os
    import sys
    executable = f"{__file__.split('cli')[0]}cli{os.sep}hq{os.sep}hq.py"
    if detached:
        from subprocess import DEVNULL
        import subprocess
        subprocess.Popen([sys.executable, executable], stdout=DEVNULL, stderr=DEVNULL)
    else:
        _hq.start()


@click.command()
@click.help_option('-h', '--help')
def stop():
    """Deactivates all agents on this machine."""
    _hq.stop()
