import os
from subprocess import check_output
from json import dumps, loads
from rich.console import Console
from test_junkie.cli.config.Config import Config
from test_junkie.cli.utils import md5

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

        def signature():
            if 'nt' in os.name:
                output = check_output('wmic csproduct get uuid'.split())
            else:
                output = check_output(
                    'hal-get-property --udi /org/freedesktop/Hal/devices/computer --key system.hardware.uuid'.split())
            return md5(str(output.decode("utf8").split()[-1]))

        server = HQ.get_server(host)
        if not os.path.exists(Config.get_hq_root_dir()):
            os.makedirs(Config.get_hq_root_dir())
        data = {"host": host, "name": name, "token": None, "id": HQ.md5(host)}

        import requests
        try:
            import socket
            response = requests.post(f"{host}/request-service-token", json={"signature": signature(),
                                                                            "hostname": socket.gethostname()})
            if response.status_code != 200 or response.json()["success"] is False:
                console.print(f"({response.status_code}) There was an issue requesting a service token. "
                              f"This is the message returned by the {host}\n{response.content.decode()}")
                exit(1)
            response = response.json()
            console.print(f"- Go to {host}/approve-service-token/{signature()}/{response['approval_token']} "
                          f"& copy the authorization token.")
            authorization_token = input("- Paste the authorization token here: ").strip()
            if len(authorization_token) > 0:
                data["token"] = authorization_token
            # TODO check that authorization token is working to prevent miss types etc
            with open(server, "w+") as doc:
                doc.write(dumps(data))
            console.print(f"{data['host']} ({data['id']}) added!")
        except requests.exceptions.ConnectionError:
            # print(traceback.format_exc())
            console.print(f"Failed to establish connection with {host}")
            exit(1)

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

            table.add_column("ID", justify="left", style="blue")
            table.add_column("Host")
            table.add_column("Name")
            table.add_column("Token", justify="left", no_wrap=True)
            table.add_column("Status", justify="left")

            for doc in docs:
                with open(Config.get_hq_root_dir() + os.sep + doc, "r+") as details:
                    server = loads(details.read())
                    table.add_row(f"{server['id']}", f"{server['host']}", f"{server['name']}", f"{server['token']}")
            console.print(table)
        else:
            console.print("Resource not found.")
