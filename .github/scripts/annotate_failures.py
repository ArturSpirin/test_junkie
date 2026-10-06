"""
Turns test failures from the saved step output into GitHub ::error annotations.
Job logs need a GitHub login to read; annotations don't - so failures stay diagnosable from the public API.
Usage: python annotate_failures.py <output file> [<output file> ...]
"""
import os
import re
import sys

ANSI = re.compile(r"\x1b\[[0-9;]*m")
# pytest -rfE summary lines, and TJ's per-suite result lines for the real test files (not the fixture suites,
# which fail on purpose)
SUMMARY = re.compile(r"^(FAILED|ERROR) |^>> \[(FAIL|ERROR)\] .* test_[a-z_]+\.")
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
        for index, line in enumerate(lines):
            if emitted >= MAX_ANNOTATIONS:
                return
            if SUMMARY.search(line):
                # the next lines carry TJ's "run #N [FAIL] :: Traceback: ..." detail
                detail = [l.strip() for l in lines[index + 1:index + 4] if l.strip().startswith("|__ run #")]
                message = line.strip() + ("\n" + "\n".join(detail) if detail else "")
                print("::error title={}::{}".format(os.path.basename(path), escape(message[:3000])))
                emitted += 1


if __name__ == "__main__":
    main(sys.argv[1:])
