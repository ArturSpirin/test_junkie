import argparse
import sys
sys.path.insert(1, "E:/Development/test_junkie/")


class CliHub(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="",
            usage="""testjunkie COMMAND

Modern Testing Framework

Commands:
run\t Run tests in any directory recursively via cmd
config\t Configure Test Junkie
""")
        parser.add_argument('command', help='command to run')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print 'test-junkie: \'{}\' is not a test-junkie command\n'.format(args.command)
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def run(self):
        parser = argparse.ArgumentParser(description='Run tests from command line',
                                         usage="testjunkie run -s SOURCE [OPTIONS]")

        parser.add_argument("-s", "--source", type=str, default=None,
                            help="Path to DIRECTORY where you have your tests. "
                                 "Test Junkie will traverse this directory looking for test suites")

        parser.add_argument("-T", "--parallel_tests", type=int, default=1,
                            help="Enables parallel test processing with allocated N number of threads")

        parser.add_argument("-S", "--parallel_suites", type=int, default=1,
                            help="Enables parallel suite processing with allocated N number of threads")

        parser.add_argument("-f", "--features", nargs="+",
                            help="Will filter out all of the tests that do not belong to the features listed")

        parser.add_argument("-c", "--components", nargs="+",
                            help="Will filter out all of the tests that do not belong to the components listed")

        parser.add_argument("-o", "--owners", nargs="+",
                            help="Will filter out all of the tests that do not belong to the owners listed")

        parser.add_argument("-m", "--mon", action="store_false",
                            help="Enables CPU & MEM monitoring")

        parser.add_argument("--html", type=basestring, default=None,
                            help="Path to FILE. This will enable HTML report generation and when ready, "
                                 "the report will be saved to the specified file")

        parser.add_argument("--xml", type=basestring, default=None,
                            help="Path to FILE. This will enable XML report generation and when ready, "
                                 "the report will be saved to the specified file")

        # now that we're inside a subcommand, ignore the first
        # TWO argvs, ie the command (git) and the subcommand (commit)
        args = parser.parse_args(sys.argv[2:])
        from test_junkie.cli.RunnerCli import RunnerCli
        tj = RunnerCli(root=args.source, ignore=[".git"])
        tj.scan()
        tj.run_suites(args)

    def config(self):
        parser = argparse.ArgumentParser(description='Allows to configure Test Junkie the way you want it')
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('--show', default=None, help="Shows the current config")
        args = parser.parse_args(sys.argv[2:])
        print args


if "__main__" == __name__:

    CliHub()
