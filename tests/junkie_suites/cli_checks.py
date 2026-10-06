"""
In-process CLI checks (tj run / audit / config / version) shared by the pytest and TJ test paths. Each check
runs the real CLI entry point with a patched sys.argv, captures stdout and the exit code, and always points
TEST_JUNKIE_HOME at a throwaway dir so the developer's real config is never touched.
"""
import contextlib
import io
import os
import re
import shutil
import sys
import tempfile

from test_junkie.constants import CliConstants

_ANSI = re.compile(r"\x1b\[[0-9;]*m")

AUDIT_SUITES = '''
from test_junkie.decorators import Suite, test
from test_junkie.listener import Listener
from test_junkie.rules import Rules


class AuditRules(Rules):
    pass


class AuditListener(Listener):
    pass


@Suite(feature="Billing", owner="alice", retry=2, meta={"area": "billing"}, rules=AuditRules,
       listener=AuditListener)
class AuditFull:

    @test(component="pay", tags=["smoke"], owner="bob", retry=2, meta={"ticket": "B-1"}, parameters=[1, 2])
    def charge(self, parameter):
        pass


@Suite(meta={"area": "suite-only"})
class AuditSuiteMetaOnly:

    @test()
    def no_meta(self):
        pass


@Suite()
class AuditBare:

    @test()
    def plain(self):
        pass
'''

PASSING_SUITE = '''
from test_junkie.decorators import Suite, test


@Suite()
class CliPassingSuite:

    @test()
    def passes(self):
        pass
'''

FAILING_SUITE = '''
from test_junkie.decorators import Suite, test


@Suite()
class CliFailingSuite:

    @test()
    def fails(self):
        assert False
'''


def run_cli(*argv):
    """
    :return: (exit code - None if the command returned normally, stdout with colors stripped)
    """
    from test_junkie.cli.cli import Cli
    home = tempfile.mkdtemp()
    previous_home, previous_argv = os.environ.get(CliConstants.HOME_ENV_VAR), sys.argv
    os.environ[CliConstants.HOME_ENV_VAR] = home
    sys.argv = ["tj"] + [str(arg) for arg in argv]
    out = io.StringIO()
    code = None
    try:
        with contextlib.redirect_stdout(out):
            Cli()
    except SystemExit as exit_:
        code = exit_.code
    finally:
        sys.argv = previous_argv
        if previous_home is None:
            del os.environ[CliConstants.HOME_ENV_VAR]
        else:
            os.environ[CliConstants.HOME_ENV_VAR] = previous_home
        shutil.rmtree(home, ignore_errors=True)
    return code, _ANSI.sub("", out.getvalue())


def _write(source, name):
    directory = tempfile.mkdtemp()
    with open(os.path.join(directory, name), "w") as doc:
        doc.write(source)
    return directory


def _audited_suites(*flags):
    code, out = run_cli("audit", "suites", "-s", _write(AUDIT_SUITES, "audit_suites.py"), *flags)
    assert code is None, out
    return sorted(set(re.findall(r"Suite: (Audit\w+)", out)))


def audit_lists_every_suite():
    assert _audited_suites() == ["AuditBare", "AuditFull", "AuditSuiteMetaOnly"]


def audit_no_flags_filter_out_suites_that_have_them():
    for flag in ("--no-rules", "--no-listeners", "--no-suite-retries", "--no-owners", "--no-features",
                 "--no-test-retries", "--no-components", "--no-tags"):
        assert "AuditFull" not in _audited_suites(flag), flag
    assert _audited_suites("--no-suite-meta") == ["AuditBare"]


def audit_no_test_meta_checks_the_tests_meta():
    # used to check the *suite's* meta, so a suite with meta but plain tests was wrongly filtered out
    assert _audited_suites("--no-test-meta") == ["AuditBare", "AuditSuiteMetaOnly"]


def audit_only_covers_the_requested_suites():
    # used to walk every suite registered in the process, so -x was ignored
    assert _audited_suites("-x", "AuditBare") == ["AuditBare"]


def audit_by_feature_and_verbose():
    code, out = run_cli("audit", "features", "-v", "-s", _write(AUDIT_SUITES, "audit_suites.py"))
    assert code is None and "Feature: Billing" in out, out


def audit_unknown_view_is_rejected():
    code, out = run_cli("audit", "nonsense", "-s", _write(AUDIT_SUITES, "audit_suites.py"))
    assert code == 120 and "is not a test-junkie command" in out, out


def audit_and_run_without_sources_explain_what_is_missing():
    for command in (["audit", "suites"], ["run"]):
        code, out = run_cli(*command)
        assert code == 120 and "Sources is a required parameter" in out, (command, out)


def audit_reports_when_nothing_matches():
    code, out = run_cli("audit", "suites", "-s", _write(AUDIT_SUITES, "audit_suites.py"), "--features", "Nope")
    assert code is None and "Nothing matches your search criteria" in out, out


def run_exit_codes():
    code, out = run_cli("run", "-s", _write(PASSING_SUITE, "passing_suite.py"), "-v")
    assert code is None, out  # returns normally = exit 0
    code, out = run_cli("run", "-s", _write(FAILING_SUITE, "failing_suite.py"))
    assert code == 1, out
    code, out = run_cli("run", "-s", tempfile.mkdtemp())  # no suites
    assert code == 1, out


def run_with_missing_config_file():
    code, out = run_cli("run", "-s", _write(PASSING_SUITE, "passing_suite.py"), "--config", "no_such_config.cfg")
    assert code == 120 and "Wasn't able to find config" in out, out


def run_import_error_and_guess_root():
    project = tempfile.mkdtemp()
    os.makedirs(os.path.join(project, "proj_helpers_tj"))
    with open(os.path.join(project, "proj_helpers_tj", "__init__.py"), "w") as doc:
        doc.write("VALUE = 1\n")
    os.makedirs(os.path.join(project, "suites"))
    with open(os.path.join(project, "suites", "needs_root.py"), "w") as doc:
        doc.write("from proj_helpers_tj import VALUE\n" + PASSING_SUITE.replace("CliPassingSuite", "NeedsRootSuite"))
    # the project root isn't importable from the suite file on its own
    code, out = run_cli("run", "-s", os.path.join(project, "suites"))
    assert code == 120 and "There is an import error" in out, out
    # --guess-root walks up from the file until the import resolves
    code, out = run_cli("run", "-s", os.path.join(project, "suites"), "--guess-root")
    assert code is None and "Trying again with assumption that this is your project root" in out, out
    sys.modules.pop("proj_helpers_tj", None)


def config_commands():
    code, out = run_cli("config", "update")
    assert "What do you want to update?" in out, out
    code, out = run_cli("config", "restore")
    assert "What do you want to restore?" in out, out
    code, out = run_cli("config", "show", "--all")
    assert "Config is located at:" in out and "[runtime]" in out, out
    code, out = run_cli("config", "show", "--sources")
    assert "sources=None" in out, out
    code, out = run_cli("config", "nonsense")
    assert "is not a test-junkie command" in out or code == 120, out


def unknown_command_and_version():
    code, out = run_cli("nonsense")
    assert code == 1 and "is not a test-junkie command" in out, out
    code, out = run_cli("version")
    assert code is None and out.startswith("Test Junkie "), out


CHECKS = [audit_lists_every_suite, audit_no_flags_filter_out_suites_that_have_them,
          audit_no_test_meta_checks_the_tests_meta, audit_only_covers_the_requested_suites, audit_by_feature_and_verbose, audit_unknown_view_is_rejected,
          audit_and_run_without_sources_explain_what_is_missing, audit_reports_when_nothing_matches,
          run_exit_codes, run_with_missing_config_file, run_import_error_and_guess_root, config_commands,
          unknown_command_and_version]
