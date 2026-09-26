import os
from tests.cli.Cmd import Cmd

ROOT = __file__.split("{0}tests".format(os.sep))[0]
EXE = ROOT + "{0}test_junkie{0}cli{0}cli.py".format(os.sep)
TESTS = ROOT + "{0}tests{0}cli_edge".format(os.sep)


def test_interrupt():

    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    print(Cmd.run(['python3', EXE, 'run', '-s', TESTS]))
