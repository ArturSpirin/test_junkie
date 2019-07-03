import subprocess
import sys
import traceback


class Cmd:

    def __init__(self):

        pass

    @staticmethod
    def run(cmd):

        try:
            try:
                out = subprocess.check_output(cmd)
            except subprocess.CalledProcessError as ex:
                out = ex.output
            if sys.version_info[0] < 3:
                output = str(out).replace("\r", "").replace("\t", "").strip().split("\n")
            else:
                output = str(out).replace("\\r", "").replace("\\t", "").strip().split("\\n")
            for i in list(output):
                if i == "" or len(i) < 2:
                    output.remove(i)
            return output
        except:
            raise Exception("Command: {} produced exception: {}".format(cmd, traceback.format_exc()))
