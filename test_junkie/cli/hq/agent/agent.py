import os
import pickle
from json import loads
from rich.console import Console
from test_junkie.cli.config.Config import Config

console = Console()


class Agent:

    def __init__(self):

        pass

    @staticmethod
    def get_agent(host):
        return f"{Config.get_agents_root_dir()}{os.sep}{Agent.md5(host)}.pickle"

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
            with open(agent, "wb") as doc:
                pickle.dump(data, doc)
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
        from glob import glob
        docs = glob(os.path.join(os.path.dirname(Config.get_agents_root_dir() + os.sep), "*.pickle"))
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
                    print(doc)
                    with open(doc, "rb") as details:
                        agent = pickle.load(details)
                        table.add_row(f"{agent['id']}",
                                      f"{agent['name']}",
                                      f"{agent['project']}",
                                      f"{agent['status']}")
            console.print(table)
        else:
            console.print("Resource not found.")
