"""
Test with multiple bazel, CodeChecker, and python versions

Pre-requisites:
    - nox
    - micromamba in PATH

How to use:
    - `nox -- test/unit` - Runs unit tests on all bazel versions
    - `nox -r` - Cache virtual environments
    - `nox -s test_full` - Runs the tests for all python, codechecker, bazel
      versions
    - For more see: https://nox.thea.codes/en/stable/usage.html
"""

import json
import nox

# This will be the list of tests that are run if none is specified
nox.options.sessions = ["test_bazel"]

# Define base environment file
MAMBA_FILE = ".ci/nox/dev.yaml"

# Define the versions we want to test against
PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13"]
CODECHECKER_VERSIONS = ["6.25", "6.26"]
BAZEL_JSON_PATH = ".github/bazel_version.json"
try:
    with open(BAZEL_JSON_PATH, "r", encoding="utf-8") as f:
        BAZEL_VERSIONS = json.load(f)
except FileNotFoundError:
    BAZEL_VERSIONS = ["6.5", "7.7"]
    print(
        f"Warning: {BAZEL_JSON_PATH} not found. "
        f"Using fallback: {BAZEL_VERSIONS}"
    )


@nox.session(venv_backend="micromamba", python=PYTHON_VERSIONS)
@nox.parametrize("codechecker", CODECHECKER_VERSIONS)
@nox.parametrize("bazel", BAZEL_VERSIONS)
def test_full(session, codechecker, bazel):
    """
    Run tests with all python, CodeChecker and Bazel versions
    """
    run_test_logic(session, bazel, codechecker)


@nox.session(venv_backend="micromamba", python="3.11")
@nox.parametrize("bazel", BAZEL_VERSIONS)
def test_bazel(session, bazel):
    """
    Run tests for all supported Bazel versions
    """
    run_test_logic(session, bazel, "6.26")


def run_test_logic(session, bazel, codechecker):
    """
    Runs tests for a specific configuration, which is provided as parameters

    :param session: Provides the nox session, specifies python version
    :param bazel: A sting containing the bazel version to be used
    :param codechecker: A string containing the CodeChecker version to be used
    """
    # Setup
    session.conda_install("--file", MAMBA_FILE)
    session.conda_install(f"bazel={bazel}", channel="conda-forge")
    session.install(f"codechecker=={codechecker}")

    # Run
    session.run("pytest", *session.posargs)
