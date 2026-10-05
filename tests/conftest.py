import atexit
import os
import shutil
import tempfile

from test_junkie.constants import CliConstants

# keep the tests, and the tj subprocesses the CLI tests start, away from the developer's real
# Test Junkie config and temp files - CLI tests run "tj config restore --all"
if not os.environ.get(CliConstants.HOME_ENV_VAR):
    _test_home = tempfile.mkdtemp(prefix="tj_test_home_")
    os.environ[CliConstants.HOME_ENV_VAR] = _test_home
    atexit.register(shutil.rmtree, _test_home, True)
