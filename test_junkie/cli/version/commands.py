import sys

import click
import pkg_resources

from test_junkie.constants import DocumentationLinks


@click.command()
@click.help_option('-h', '--help')
def version():
    """Display the current version."""
    print("Test Junkie {} (Python{})\n{}".format(pkg_resources.require("test-junkie")[0].version,
                                                 sys.version_info[0],
                                                 DocumentationLinks.DOMAIN))
