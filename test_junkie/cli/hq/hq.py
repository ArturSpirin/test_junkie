import os
from json import dumps, loads

from rich.console import Console

from test_junkie.cli.config import Config

console = Console()


class HQ:

    def __init__(self):

        pass

    @staticmethod
    def get_server(host):
        return f"{Config.get_hq_root_dir()}{os.sep}{HQ.md5(host)}.json"

    @staticmethod
    def md5(host):
        import hashlib
        m = hashlib.md5()
        m.update(host.encode("utf8"))
        return m.hexdigest()

    @staticmethod
    def add(host, name):
        server = HQ.get_server(host)
        if not os.path.exists(Config.get_hq_root_dir()):
            os.makedirs(Config.get_hq_root_dir())
        data = {"host": host, "name": name, "token": None, "id": HQ.md5(host)}
        console.print(f"1. Go to {host}/new/{data['id']} & copy the authorization token.")
        token = input("2. Paste the authorization token here: ").strip()
        if len(token) > 0:
            data["token"] = "response.json()['token']"
        with open(server, "w+") as doc:
            doc.write(dumps(data))
        console.print(f"{data['host']} ({data['id']}) added!")

    @staticmethod
    def details(hq):

        if not os.path.exists(Config.get_hq_root_dir()):
            return None
        docs = os.listdir(Config.get_hq_root_dir())
        if docs:
            for doc in docs:
                with open(Config.get_hq_root_dir() + os.sep + doc, "r+") as details:
                    server = loads(details.read())
                    if hq == server["name"] or hq == server["host"] or hq == server["id"]:
                        return server
        else:
            return None

    @staticmethod
    def remove(hq):
        from test_junkie.cli.hq.agent.agent import Agent
        agents = Agent.agents_by_hq(hq)
        if agents:
            console.print(f"Can't remove \"{hq}\", it is currently hosting {len(agents)} agent(s):")
            for agent in agents:
                console.print(f"- {agent['id']}")
            exit(1)
        if not os.path.exists(Config.get_hq_root_dir()):
            console.print("Resource not found.")
            exit(0)
        docs = os.listdir(Config.get_hq_root_dir())
        if docs:
            for doc in docs:
                match = False
                with open(Config.get_hq_root_dir() + os.sep + doc, "r+") as details:
                    server = loads(details.read())
                    if hq == server["name"] or hq == server["host"] or hq == server["id"]:
                        match = True

                if match:
                    os.remove(Config.get_hq_root_dir() + os.sep + doc)
                    print(f"Removed: {hq}")
                    exit(0)
        else:
            console.print("Resource not found.")

    @staticmethod
    def ls():

        if not os.path.exists(Config.get_hq_root_dir()):
            console.print("Resource not found.")
            exit(0)
        docs = os.listdir(Config.get_hq_root_dir())
        if docs:
            from rich.table import Table

            table = Table(title="")

            table.add_column("id", justify="left", style="blue")
            table.add_column("host")
            table.add_column("name")
            table.add_column("token", justify="left", no_wrap=True)
            table.add_column("status", justify="left")

            for doc in docs:
                with open(Config.get_hq_root_dir() + os.sep + doc, "r+") as details:
                    server = loads(details.read())
                    table.add_row(f"{server['id']}", f"{server['host']}", f"{server['name']}", f"{server['token']}")
            console.print(table)
        else:
            console.print("Resource not found.")
