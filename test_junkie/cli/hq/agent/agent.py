import os
import platform
import socket
import sys
import time
from datetime import datetime
from glob import glob
from json import dumps, loads

import pkg_resources
import requests
from rich.console import Console
from test_junkie.cli.config.Config import Config

console = Console()


class Agent:

    def __init__(self):

        pass

    @staticmethod
    def get_agent(host):
        return f"{Config.get_agents_root_dir()}{os.sep}{Agent.md5(host)}.json"

    @staticmethod
    def md5(host):
        import hashlib
        m = hashlib.md5()
        m.update(host.encode("utf8"))
        return m.hexdigest()

    @staticmethod
    def add(hq, project, name):
        agent = Agent.get_agent(project)
        if not os.path.exists(Config.get_agents_root_dir()):
            os.makedirs(Config.get_agents_root_dir())
        from test_junkie.cli.hq.hq import HQ
        server = HQ.details(hq)
        if server:
            data = {"project": project, "name": name, "hq": server, "id": Agent.md5(server["id"]+project), "status": None}
            with open(agent, "w+") as doc:
                doc.write(dumps(data))
            console.print(f"Deployed agent to {data['project']}!")
        else:
            console.print(f"{hq} resource not found!")

    @staticmethod
    def details(agent):
        if not os.path.exists(Config.get_agents_root_dir()):
            return None
        docs = os.listdir(Config.get_agents_root_dir())
        if docs:
            for doc in docs:
                with open(Config.get_agents_root_dir() + os.sep + doc, "r+") as details:
                    data = loads(details.read())
                    if agent == data["name"] or agent == data["id"]:
                        return data
        else:
            return None

    @staticmethod
    def agents_by_hq(hq):
        if not os.path.exists(Config.get_agents_root_dir()):
            return []
        docs = os.listdir(Config.get_agents_root_dir())
        agents = []
        if docs:
            for doc in docs:
                with open(Config.get_agents_root_dir() + os.sep + doc, "r+") as details:
                    agent = loads(details.read())
                    if hq == agent["hq"]["name"] or hq == agent["hq"]["id"]  or hq == agent["hq"]["host"]:
                        agents.append(agent)
        return agents

    @staticmethod
    def remove(agent):

        if not os.path.exists(Config.get_agents_root_dir()):
            console.print("Resource not found.")
            exit(0)
        docs = os.listdir(Config.get_agents_root_dir())
        if docs:
            for doc in docs:
                match = False
                with open(Config.get_agents_root_dir() + os.sep + doc, "r+") as details:
                    server = loads(details.read())
                    if agent == server["name"] or agent == server["id"]:
                        match = True

                if match:
                    os.remove(Config.get_agents_root_dir() + os.sep + doc)
                    print(f"Removed: {agent}")
                    exit(0)
        else:
            console.print("Resource not found.")

    @staticmethod
    def ls(hq):
        if not os.path.exists(Config.get_agents_root_dir()):
            console.print("Resource not found.")
            exit(0)
        docs = os.listdir(Config.get_agents_root_dir())
        if docs:
            from rich.table import Table

            table = Table(title="")

            table.add_column("ID", justify="left", style="blue")
            table.add_column("Name")
            table.add_column("Project", justify="left", no_wrap=True)
            table.add_column("Status", justify="left")
            if hq is not None:
                agents = Agent.agents_by_hq(hq)
                if agents:
                    for agent in agents:
                        table.add_row(f"{agent['id']}",
                                      f"{agent['name']}",
                                      f"{agent['project']}",
                                      f"{agent['status']}")
                else:
                    console.print("Resource not found.")
                    exit(0)
            else:
                for doc in docs:
                    with open(Config.get_agents_root_dir() + os.sep + doc, "r+") as details:
                        agent = loads(details.read())
                        table.add_row(f"{agent['id']}",
                                      f"{agent['name']}",
                                      f"{agent['project']}",
                                      f"{agent['status']}")
            console.print(table)
        else:
            console.print("Resource not found.")

    @staticmethod
    def start():

        try:
            while True:
                for dirName, subdirList, fileList in os.walk(Config.get_agents_root_dir(), topdown=True):
                    for file_path in glob(os.path.join(os.path.dirname(dirName + "\\"), "*.json")):
                        with open(file_path, "r") as doc:
                            config = loads(doc.read())
                            host, port, source = config["host"], config["port"], [config["project_root"]]

                            from test_junkie.cli.run.cli_runner import CliRunner
                            tj = CliRunner(sources=source, ignore=[".git"], suites=None)
                            tj.scan()

                            from test_junkie.cli.audit.cli_audit import CliAudit
                            aggregator = CliAudit(suites=tj.suites, args=None)
                            aggregator.aggregate()
                            tests = aggregator.aggregated_data["test_roster"]
                            tjv = pkg_resources.require("test-junkie")[0].version
                            pyv = sys.version_info[0]
                            payload = {"host": socket.gethostname(),
                                       "tests": tests,
                                       "project": source[0].split(os.sep)[-1],
                                       "project_location": source[0],
                                       "tech": {"name": "Test Junkie {} (Python{})".format(tjv, pyv),
                                                "tjv": tjv,
                                                "pyv": pyv,
                                                "platform": {"os": platform.system(), "release": platform.release()}},
                                       "sent_at": str(datetime.now())}
                            if tests:  # TODO add auth
                                endpoint = "{host}:{port}/handler".format(host=host, port=port)
                                try:
                                    response = requests.post(endpoint, json=payload)
                                    print(">>>>>", response.status_code)
                                except Exception as error:
                                    print(error)
                            else:
                                print("No data to send: ", tests)
                time.sleep(20)
        except KeyboardInterrupt:
            print("Ctrl + C. Exiting!")
