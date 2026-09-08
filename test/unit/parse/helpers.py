# Copyright 2026 Ericsson AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Shared helpers for the parse and store verification scripts.
"""

import os
import subprocess
import sys

# Basename of the analysis output directory produced by codechecker_test.
REPORT_DIR_NAME = "codechecker-files"

def resolve_report_data(paths: list[str]) -> str:
    """Return the data subdirectory that CodeChecker parse consumes.

    Bazel passes every output of the analysis target via $(rootpaths); the
    report directory is the one ending in "codechecker-files", and the plist
    reports live in its "data" subdirectory.
    """
    # pylint: disable=duplicate-code
    report_dirs = [p for p in paths if os.path.basename(p) == REPORT_DIR_NAME]
    if not report_dirs:
        print(f"FAILED: no {REPORT_DIR_NAME} directory in paths: {paths}")
        sys.exit(1)
    data_dir = os.path.join(report_dirs[0], "data")
    if not os.path.isdir(data_dir):
        print(f"FAILED: report data directory not found at {data_dir}")
        sys.exit(1)
    return data_dir


def run_codechecker(arguments: list[str]) -> tuple[int, str, str]:
    """Run a CodeChecker command and return (exit_code, stdout, stderr)."""
    # pylint: disable=duplicate-code
    command = ["CodeChecker"] + arguments
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr
