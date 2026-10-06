"""
Helpers for config round-trip tests, shared by the pytest and TJ test paths.
"""
import os

from test_junkie.cli.cli_config import Config
from test_junkie.cli.cli_runner import CliRunner
from test_junkie.constants import CliConstants, Undefined
from test_junkie.settings import Settings

# how a config written by tj <= 0.9a2 stored plain strings and booleans: unquoted
LEGACY_LINES = ["html_report=report.html", "xml_report=reports/out.xml", "guess_root=False"]


def make_config(directory, extra_lines=()):
    """
    :return: STRING path to a fresh config file with the default settings plus extra_lines
    """
    lines = CliConstants.DEFAULTS.strip("\n").split("\n")
    for extra in extra_lines:
        key = extra.split("=")[0] + "="
        lines = [extra if line.startswith(key) else line for line in lines]
        if extra not in lines:
            lines.append(extra)
    path = os.path.join(directory, "tj_test.cfg")
    with open(path, "w") as doc:
        doc.write("\n".join(lines) + "\n")
    return path


def runtime_settings(config_path):
    return Settings(runner_kwargs={"config": config_path}, run_kwargs={})


def cli_runner(config_path):
    return CliRunner(sources=["."], ignore=[".git"], suites=None, code_cov=False, cov_rcfile=Undefined,
                     guess_root=Undefined, config=config_path)


def save(config_path, **values):
    config = Config(config_name=config_path)
    for option, value in values.items():
        config.set_value(option, value)
