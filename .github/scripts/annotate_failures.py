"""
Turns pytest failures from the saved step output into GitHub ::error annotations. The test_junkie path doesn't
need this: tj run prints its own annotations when GITHUB_ACTIONS is set.
Job logs need a GitHub login to read; annotations don't - so failures stay diagnosable from the public API.
Usage: python annotate_failures.py <output file> [<output file> ...]
"""
import os
import re
import sys

ANSI = re.compile(r"\x1b\[[0-9;]*m")
SUMMARY = re.compile(r"^(FAILED|ERROR) ")  # pytest -rfE summary lines
MAX_ANNOTATIONS = 25


def escape(message):
    return message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def main(paths):
    emitted = 0
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as doc:
            lines = [ANSI.sub("", line.rstrip("\n")) for line in doc]
        for line in lines:
            if emitted >= MAX_ANNOTATIONS:
                return
            if SUMMARY.search(line):
                print("::error title={}::{}".format(os.path.basename(path), escape(line.strip()[:3000])))
                emitted += 1


if __name__ == "__main__":
    main(sys.argv[1:])
