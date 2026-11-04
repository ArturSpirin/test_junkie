import os
import subprocess
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = sys.executable  # the interpreter under test, not whatever `python3` is on PATH


class Cmd:

    def __init__(self):

        pass

    @staticmethod
    def run(cmd):

        try:
            # put the checkout first so the CLI imports the branch's code, not an installed copy
            env = dict(os.environ, PYTHONPATH=ROOT + (os.pathsep + os.environ["PYTHONPATH"]
                                                      if os.environ.get("PYTHONPATH") else ""))
            try:
                out = subprocess.check_output(cmd, env=env)
            except subprocess.CalledProcessError as ex:
                out = ex.output
            output = str(out).replace("\\r", "").replace("\\t", "").strip().split("\\n")
            for i in list(output):
                if i == "" or len(i) < 2:
                    output.remove(i)
            return output
        except:
            raise Exception("Command: {} produced exception: {}".format(cmd, traceback.format_exc()))
