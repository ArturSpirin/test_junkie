import os
import pickle
import sys
import platform
from subprocess import check_output
from json import dumps, loads
from rich.console import Console
from test_junkie.cli.config.Config import Config
from test_junkie.cli.utils import md5
from test_junkie.constants import Undefined

console = Console()


class HQ:

    __LOCK_FILE = f"{Config.get_agents_root_dir()}{os.sep}enable_agents.lock"

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
    def ls(display_tokens=False):

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
            if display_tokens:
                table.add_column("Token", justify="left", no_wrap=True)
            table.add_column("Status", justify="left")

            for doc in docs:
                with open(Config.get_hq_root_dir() + os.sep + doc, "r+") as details:
                    server = loads(details.read())
                    if display_tokens:
                        table.add_row(f"{server['id']}", f"{server['host']}", f"{server['name']}", f"{server['token']}")
                    else:
                        table.add_row(f"{server['id']}", f"{server['host']}", f"{server['name']}")
            console.print(table)
        else:
            console.print("Resource not found.")

    @staticmethod
    def __is_enabled():
        return os.path.exists(HQ.__LOCK_FILE)

    @staticmethod
    def __add_lock():
        if not HQ.__is_enabled():
            with open(HQ.__LOCK_FILE, "w+") as file:
                file.write("")

    @staticmethod
    def __remove_lock():
        if os.path.exists(HQ.__LOCK_FILE):
            return os.remove(HQ.__LOCK_FILE)

    @staticmethod
    def status():

        if HQ.__is_enabled():
            console.print("[[[bold green]ENABLED[/bold green]]] Agents on this machine are enabled and sending data "
                          "to their respective Test Junkie HQ instances.")
            return True
        else:
            console.print("[[[bold red]DISABLED[/bold red]]] Agents on this machine are disabled and will NOT send data"
                          " to their respective Test Junkie HQ instances.")
            return False

    @staticmethod
    def start():

        from test_junkie.cli.run.cli_runner import CliRunner
        from test_junkie.cli.audit.cli_audit import CliAudit
        import pkg_resources
        import socket
        from datetime import datetime
        import requests
        import time
        if not HQ.__is_enabled():
            HQ.__add_lock()
            try:
                while HQ.__is_enabled():
                    for dirName, subdirList, fileList in os.walk(Config.get_agents_root_dir(), topdown=True):
                        from glob import glob
                        for file_path in glob(os.path.join(os.path.dirname(dirName + "\\"), "*.pickle")):
                            with open(file_path, "rb") as doc:
                                agent = pickle.load(doc)
                                host, token, source = agent["hq"]["host"], agent["hq"]["token"], [agent["project"]]

                                tj = CliRunner(sources=source, ignore=[".git"], suites=None)
                                tj.scan()

                                aggregator = CliAudit(suites=tj.suites, args=Undefined)
                                aggregator.aggregate()
                                tests = aggregator.aggregated_data["test_roster"]
                                test_junkie_version = pkg_resources.require("test-junkie")[0].version
                                python_version = sys.version_info[0]
                                payload = {"host": socket.gethostname(),
                                           "tests": tests,
                                           "project": source[0].split(os.sep)[-1],
                                           "project_location": source[0],
                                           "tech": {"name": f"Test Junkie {test_junkie_version} "
                                                            f"(Python{python_version})",
                                                    "tjv": test_junkie_version,
                                                    "pyv": python_version,
                                                    "platform": {"os": platform.system(),
                                                                 "release": platform.release()}},
                                           "sent_at": str(datetime.now())}
                                if tests:  # TODO add auth
                                    endpoint = f"{host}/handler?token={token}"
                                    try:
                                        response = requests.post(endpoint, json=payload)
                                        print(">>>>>", response.status_code)
                                    except Exception as error:
                                        print(error)
                                else:
                                    print("No data to send: ", tests)
                    time.sleep(20)
            except KeyboardInterrupt:
                HQ.__remove_lock()
                print("Ctrl + C. Exiting!")

    @staticmethod
    def stop():
        HQ.__remove_lock()


if "__main__" == __name__:

    HQ.start()
