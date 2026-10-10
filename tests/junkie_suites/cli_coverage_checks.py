"""
CLI checks for the branches the main CLI checks (cli_checks.py) don't reach: config/audit edge cases, the
interactive scan line, Ctrl+C at the less common points, settings that come from the saved config. Shared by the
pytest and TJ test paths, and run in-process through cli_checks.run_cli like the rest.
"""
import contextlib
import io
import os
import runpy
import sys
import tempfile
import warnings

from tests.junkie_suites.cli_checks import AUDIT_SUITES, COVERAGE_RC, PASSING_SUITE, _ANSI, _write, run_cli
from test_junkie.constants import CliConstants

CONFLICT_SUITES = '''
from test_junkie.decorators import Suite, test


@Suite()
class CovConflictWriter:

    @test(conflicts_with=["CovConflictReader.reads"])
    def writes(self):
        pass


@Suite()
class CovConflictReader:

    @test()
    def reads(self):
        pass
'''

BAD_CONFLICT_SUITE = '''
from test_junkie.decorators import Suite, test


@Suite()
class CovBadConflict:

    @test(conflicts_with=["CovNoSuchSuite.nope"])
    def a(self):
        pass
'''

# fails to import the first time, and is interrupted when --guess-root loads it again
INTERRUPTED_GUESS_ROOT = '''
import os
if os.environ.get("TJ_COV_GUESS_ROOT_RETRY"):
    raise KeyboardInterrupt
os.environ["TJ_COV_GUESS_ROOT_RETRY"] = "1"
raise ImportError("first load fails")

from test_junkie.decorators import Suite, test


@Suite()
class CovGuessRootInterrupted:

    @test()
    def never(self):
        pass
'''

NOT_A_SUITE = '''raise RuntimeError("a file that doesn't mention the framework must not be imported by the scan")
'''


class _Tty(io.StringIO):

    def isatty(self):
        return True


def _run_cli_tty(*argv):
    """run_cli, but with a stdout that says it's a terminal (run_cli's own stdout never is)"""
    from test_junkie.cli.cli import Cli
    home = tempfile.mkdtemp()
    previous_home, previous_argv = os.environ.get(CliConstants.HOME_ENV_VAR), sys.argv
    os.environ[CliConstants.HOME_ENV_VAR] = home
    sys.argv = ["tj"] + [str(arg) for arg in argv]
    out = _Tty()
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
    return code, out.getvalue()


def _toml_available():
    try:
        import tomllib  # noqa: F401
    except ImportError:
        try:
            import tomli  # noqa: F401
        except ImportError:
            return False
    return True


def config_flag_without_a_file_and_config_help():
    code, out = run_cli("config", "show", "--config")
    assert code == 120 and "--config needs a file" in out and "Nothing was changed." in out, out
    for flag in ("-h", "--help"):
        code, out = run_cli("config", flag)
        assert code is None and "usage:" in out and "show" in out and "update" in out, out


def config_rejects_an_unknown_option():
    code, out = run_cli("config", "update", "--no-such-option")
    assert code == 120 and "Unrecognized arguments: --no-such-option." in out and "Nothing was saved." in out, out


def cli_module_runs_as_a_script():
    from test_junkie.cli.cli import CliUtils
    assert "bold" in CliUtils.format_bold_string("bold"), CliUtils.format_bold_string("bold")
    home = tempfile.mkdtemp()
    previous_home, previous_argv = os.environ.get(CliConstants.HOME_ENV_VAR), sys.argv
    os.environ[CliConstants.HOME_ENV_VAR] = home
    sys.argv = ["tj", "version"]
    out = io.StringIO()
    code = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # runpy: already imported as test_junkie.cli.cli
            with contextlib.redirect_stdout(out):
                runpy.run_module("test_junkie.cli.cli", run_name="__main__")
    except SystemExit as exit_:
        code = exit_.code
    finally:
        sys.argv = previous_argv
        if previous_home is None:
            del os.environ[CliConstants.HOME_ENV_VAR]
        else:
            os.environ[CliConstants.HOME_ENV_VAR] = previous_home
    assert code in (None, 0) and "Test Junkie" in _ANSI.sub("", out.getvalue()), out.getvalue()


def audit_owner_and_component_filters():
    directory = _write(AUDIT_SUITES, "audit_suites.py")
    for flags in (("-o", "bob"), ("-c", "pay")):
        code, out = run_cli("audit", "suites", "-s", directory, *flags)
        assert code is None and "AuditFull" in out, out
        assert "AuditSuiteMetaOnly" not in out and "AuditBare" not in out, (flags, out)
    code, out = run_cli("audit", "suites", "-s", directory, "-o", "nobody")
    assert code is None and "AuditFull" not in out, out


def audit_conflicts_view():
    import json
    code, out = run_cli("audit", "conflicts", "-s", _write(AUDIT_SUITES, "audit_suites.py"))
    assert code is None and "No conflicts declared." in out and "conflicts" in out, out
    code, out = run_cli("audit", "conflicts", "-s", _write(CONFLICT_SUITES, "cov_conflicts.py"))
    assert code is None and "CovConflictReader.reads  x  CovConflictWriter.writes" in out, out
    directory = _write(BAD_CONFLICT_SUITE, "cov_bad_conflict.py")
    code, out = run_cli("audit", "conflicts", "-s", directory)
    assert code == 1 and "conflicts_with problem:" in out and "CovNoSuchSuite.nope" in out, out
    code, out = run_cli("audit", "conflicts", "-s", directory, "--json")
    assert code == 1 and "CovNoSuchSuite.nope" in json.loads(out)["error"], out


def interactive_scan_shows_progress_then_clears_it():
    directory = _write(AUDIT_SUITES, "audit_suites.py")
    code, out = _run_cli_tty("audit", "suites", "-s", directory)
    assert code is None, out
    assert "scanning {} …".format(directory) in out and "\r\x1b[2K" in out, repr(out[:300])
    assert out.index("\r\x1b[2K") > out.index("scanning"), repr(out[:300])
    code, out = _run_cli_tty("audit", "suites", "-s", directory, "--json")  # JSON output: no progress line
    assert code is None and "scanning" not in out, repr(out[:300])


def scan_skips_files_that_dont_mention_the_framework():
    directory = _write(PASSING_SUITE, "passing_suite.py")
    with open(os.path.join(directory, "helpers_tj_cov.py"), "w") as doc:
        doc.write(NOT_A_SUITE)
    code, out = run_cli("run", "-s", directory)
    assert code is None and "1 suite, 1 test" in out and "must not be imported" not in out, out


def ctrl_c_while_guessing_the_root():
    directory = _write(INTERRUPTED_GUESS_ROOT, "cov_interrupted_guess.py")
    try:
        code, out = run_cli("run", "-s", directory, "--guess-root", cwd=directory)
        # 120, not 12: the exit(12) is caught by the scan's bare except and reported as an unexpected error
        assert code in (12, 120) and "Trying again with assumption" in out and "(Ctrl+C) Exiting!" in out, out
    finally:
        os.environ.pop("TJ_COV_GUESS_ROOT_RETRY", None)


def ctrl_c_before_the_run_reports_it():
    import test_junkie.cli.cli_runner as cli_runner

    class Interrupted:
        def __init__(self, **kwargs):
            raise KeyboardInterrupt  # no tj_reported: the run never got to say it was cancelled

    original = cli_runner.Runner
    cli_runner.Runner = Interrupted
    try:
        code, out = run_cli("run", "-s", _write(PASSING_SUITE, "passing_suite.py"))
    finally:
        cli_runner.Runner = original
    assert code == 12 and "(Ctrl+C) Exiting!" in out, out


def project_root_retry_that_still_fails():
    project = tempfile.mkdtemp()
    os.makedirs(os.path.join(project, "suites"))
    with open(os.path.join(project, "suites", "needs_missing.py"), "w") as doc:
        doc.write("import cov_missing_module_tj\n" + PASSING_SUITE.replace("CliPassingSuite", "CovNeedsMissing"))
    saved = list(sys.path)
    sys.path[:] = [entry for entry in sys.path if entry not in ("", ".")]  # like the tj command, not python -m
    try:
        code, out = run_cli("config", "update", "-T", "1", "--config", "./tj.cfg", cwd=project)
        assert code is None, out
        # the import fails, is retried with the tj.cfg folder on sys.path, and fails again
        code, out = run_cli("run", "-s", "suites", cwd=project)
        assert code == 120 and "There is an import error" in out and "cov_missing_module_tj" in out, out
    finally:
        sys.path[:] = saved


def code_coverage_and_guess_root_from_the_saved_config():
    directory = _write(PASSING_SUITE, "passing_suite.py")
    rcfile = os.path.join(directory, "cov.rc")
    with open(rcfile, "w") as doc:
        doc.write(COVERAGE_RC)
    home = tempfile.mkdtemp()
    code, out = run_cli("config", "update", "--code-cov", "--cov-rcfile", rcfile, home=home, keep_home=True)
    assert code is None, out
    # own working dir, so the inner coverage session doesn't use the repo's .coveragerc or write into it
    code, out = run_cli("run", "-s", directory, home=home, cwd=directory)
    assert code is None and "Code coverage report:" in out and "code_cov on" in out and "cov_rcfile" in out, out
    # a saved guess_root: a suite that imports from the project root loads without --guess-root
    project = tempfile.mkdtemp()
    os.makedirs(os.path.join(project, "cov_root_helpers_tj"))
    with open(os.path.join(project, "cov_root_helpers_tj", "__init__.py"), "w") as doc:
        doc.write("VALUE = 1\n")
    os.makedirs(os.path.join(project, "suites"))
    with open(os.path.join(project, "suites", "cov_needs_root.py"), "w") as doc:
        doc.write("from cov_root_helpers_tj import VALUE\n" + PASSING_SUITE.replace("CliPassingSuite", "CovNeedsRoot"))
    home = tempfile.mkdtemp()
    code, out = run_cli("config", "update", "--guess-root", home=home, keep_home=True)
    assert code is None, out
    saved = list(sys.path)
    sys.path[:] = [entry for entry in sys.path if entry not in ("", ".")]
    try:
        code, out = run_cli("run", "-s", os.path.join(project, "suites"), home=home)
        assert code is None and "Trying again with assumption that this is your project root" in out, out
        assert "1 suite, 1 test" in out and "[PASSED]" in out, out
    finally:
        sys.path[:] = saved
        sys.modules.pop("cov_root_helpers_tj", None)


def pyproject_without_a_toml_reader_or_with_bad_toml():
    from test_junkie.cli.cli_config import Config
    project = tempfile.mkdtemp()
    with open(os.path.join(project, "pyproject.toml"), "w") as doc:
        doc.write('[tool.test_junkie]\nsources = ["."]\n')
    saved = {name: sys.modules.get(name, Undefined_) for name in ("tomllib", "tomli")}
    for name in saved:
        sys.modules[name] = None  # import fails as on Python 3.9/3.10 without tomli
    try:
        assert Config.project_path(project) is None
    finally:
        for name, module in saved.items():
            if module is Undefined_:
                del sys.modules[name]
            else:
                sys.modules[name] = module
    if not _toml_available():
        return
    assert Config.project_path(project) == os.path.join(project, "pyproject.toml")
    try:
        import tomllib as reader
    except ImportError:
        import tomli as reader
    sys.modules["tomllib"], sys.modules["tomli"] = None, reader  # no tomllib: tomli is used instead
    try:
        assert Config.project_path(project) == os.path.join(project, "pyproject.toml")
    finally:
        for name, module in saved.items():
            if module is Undefined_:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    config = Config(os.path.join(project, "pyproject.toml"))
    try:
        config.set_value("test_multithreading_limit", 2)
        raise AssertionError("tj config wrote to a pyproject.toml")
    except ValueError as error:
        assert "read-only for tj config" in str(error), error
    with open(os.path.join(project, "pyproject.toml"), "w") as doc:
        doc.write("[tool.test_junkie\nnot toml at all\n")
    assert Config.project_path(project) is None


Undefined_ = object()

CHECKS = [config_flag_without_a_file_and_config_help, config_rejects_an_unknown_option, cli_module_runs_as_a_script,
          audit_owner_and_component_filters, audit_conflicts_view, interactive_scan_shows_progress_then_clears_it,
          scan_skips_files_that_dont_mention_the_framework, ctrl_c_while_guessing_the_root,
          ctrl_c_before_the_run_reports_it, project_root_retry_that_still_fails,
          code_coverage_and_guess_root_from_the_saved_config, pyproject_without_a_toml_reader_or_with_bad_toml]
