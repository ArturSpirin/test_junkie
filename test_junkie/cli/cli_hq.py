import argparse
import os
import pickle
import socket
import time
from base64 import b64encode
from datetime import datetime
from glob import glob
from json import dumps, loads

import requests

from test_junkie.cli.cli_config import Config


class TestJunkieHQ:

    def __init__(self, command, args):
        # print(command)
        # print(args)
        if command in ["agent", "master"]:
            getattr(self, command)(args)

    def agent(self, args):

        return TestJunkieHQAgent(args)

    def master(self, args):

        return TestJunkieHQMaster(args)


class TestJunkieHQMaster:
    # TODO simulated manually at the moment but need to finish implementation
    def __init__(self, args):
        parser = argparse.ArgumentParser(description="",
                                         usage="""tj hq COMMAND

This allows to set up the Test Junkie HQ application and the underlying services 
which can be integrated with Test Junkie HQ Agents.

Commands:
init\t Initiate a new Test Junkie HQ application on this node.
remove\t Removes the Test Junkie HQ application from this node.
show\t Show information regarding Test Junkie HQ on this node, related agents, and processes.

Use: tj hq COMMAND -h to display COMMAND specific help
""")
        parser.add_argument('command', help='command to run')
        self.args = args[1:]
        self.parsed_args = parser.parse_args(args[:1])
        getattr(self, self.parsed_args.command)()

    def init(self):

        print("Test Junkie HQ initialized!")

    def remove(self):

        print("Test Junkie HQ removed!")

    def show(self):

        print("Test Junkie HQ is awesome!")


class TestJunkieHQAgent:

    def __init__(self, args):

        parser = argparse.ArgumentParser(description="",
                                         usage="""tj hq agent COMMAND

Configure a Test Junkie agent for any of your repositories that use Test Junkie test definitions.

Commands:
add\t Add a new Test Junkie agent to a repository or overwrite existing one
remove\t Remove Test Junkie agent from a repository
show\t Show all current agents that are deployed in all of the repositories on this node
start\t Activates all Agents on the node

Use: tj hq agent COMMAND -h to display COMMAND specific help
""")
        parser.add_argument('command', help='command to run')
        self.args = args[1:]
        self.parsed_args = parser.parse_args(args[:1])
        getattr(self, self.parsed_args.command)()

    def add(self):
        parser = argparse.ArgumentParser(description="",
                                         usage="""tj hq agent add PROJECT

Add a new Test Junkie Agent to a repository or overwrite existing one.

Use: tj hq agent add PROJECT
""")
        parser.add_argument('project', help='Full path to the root directory of your project/repository')
        parser.add_argument('--host', type=str, help='Host address where Test Junkie HQ is running', required=True)
        parser.add_argument('--port', type=int, help='Porn on which Test Junkie HQ is running', required=True)
        # parser.add_argument('tj-config', help='Agent will process data according to the config settings')
        args = parser.parse_args(self.args)
        file_path = "{}/{}.json".format(Config.get_agents_root_dir(), b64encode(args.project))
        if not os.path.exists(Config.get_agents_root_dir()):
            os.makedirs(Config.get_agents_root_dir())
        with open(file_path, "w+") as doc:
            data = {"project_root": args.project, "host": args.host, "port": args.port}
            doc.write(dumps(data))

        print("Test Junkie Agent added to: {}!".format(args.project))

    def remove(self):
        print("Test Junkie Agent removed from: !")

    def show(self):
        print("Test Junkie HQ is awesome!")

    def start(self):

        try:
            while True:
                for dirName, subdirList, fileList in os.walk(Config.get_agents_root_dir(), topdown=True):
                    for file_path in glob(os.path.join(os.path.dirname(dirName + "\\"), "*.json")):
                        with open(file_path, "r") as doc:
                            config = loads(doc.read())
                            host, port, source = config["host"], config["port"], [config["project_root"]]

                            from test_junkie.cli.cli_runner import CliRunner
                            tj = CliRunner(sources=source, ignore=[".git"], suites=None)
                            tj.scan()

                            from test_junkie.cli.cli_audit import CliAudit
                            aggregator = CliAudit(suites=tj.suites, args=None)
                            aggregator.aggregate()
                            tests = aggregator.aggregated_data["test_roster"]
                            payload = {"host": socket.gethostname(),
                                       "tests": tests,
                                       "project": source[0].split(os.sep)[-1],
                                       "sent_at": str(datetime.now())}
                            if tests:  # TODO add auth
                                endpoint = "{host}:{port}/handler".format(host=host, port=port)
                                response = requests.post(endpoint, json=payload)
                                print(response)
                            else:
                                print("No data to send: ", tests)

                time.sleep(500)
        except KeyboardInterrupt:
            print("Ctrl + C. Exiting!")
