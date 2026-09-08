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
Self-contained store verification script for Bazel py_test targets.

Starts its own CodeChecker server on a free port, stores the report files
produced by a codechecker_test target (supplied as a data dependency), and
asserts that the store command succeeds. The server is always torn down and
its temporary workspace removed, even on failure.

The embedded CodeCheckerServer helper (and its supporting functions) is a copy
of test/common/codechecker_server.py so that this test is self-contained and
does not depend on test/common.

Usage:
    python store_check.py --name unit_test_bazel <rootpaths...>
"""

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib
import urllib.error
import urllib.request

# helpers is the ":helpers" py_library, imported as a top-level module at
# runtime under Bazel. pylint runs outside Bazel and cannot resolve it
# statically, so silence the false positive here.
# pylint: disable=import-error
from helpers import resolve_report_data, run_codechecker


def _get_free_port():
    """
    Return a port number that is free
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def wait_codechecker_server(
    product: str = "Default",
    host: str = "localhost",
    port: int = 8001,
    timeout: int = 10000,
    attempt_every: int = 100,
) -> bool:
    """
    Wait until the product is available in the CodeChecker server
    """
    start = time.monotonic()
    url = f"http://{host}:{port}/{product}"
    while time.monotonic() - start < timeout / 1000:
        try:
            with urllib.request.urlopen(url, timeout=timeout / 1000) as resp:
                if resp.getcode() == 200:
                    return True
        except (urllib.error.URLError, urllib.error.HTTPError):
            pass
        time.sleep(attempt_every / 1000)
    return False


class CodeCheckerServer:
    """
    CodeCheckerServer object for testing.
    Cleans up after itself.
    """

    def __init__(self, port=None):
        self.running = False
        self.port = port if port else _get_free_port()
        self.temp_workspace = tempfile.mkdtemp()
        self.start_codechecker_server()

    def __del__(self):
        self.stop_codechecker_server()

    def start_codechecker_server(self):
        """
        Starts a CodeChecker server instance on a free port
        This server must be shutdown with stop_codechecker_sever
        """
        if self.running:
            return
        server_command = [
            "CodeChecker",
            "server",
            "--workspace",
            self.temp_workspace,
            "--port",
            str(self.port),
        ]
        # These file/popen processes are closed when the object dies
        # pylint: disable=consider-using-with
        self.devnull = open(os.devnull, "w", encoding="utf-8")
        # pylint: disable=consider-using-with
        self.server_process: subprocess.Popen = subprocess.Popen(
            server_command, stdout=self.devnull
        )
        assert wait_codechecker_server(
            port=self.port, timeout=10000
        ), "Failed to start CodeChecker server"
        self.running = True

    def stop_codechecker_server(self):
        """
        Stops the CodeChecker server started by start_codechecker_server
        """
        # Idempotent: the object is also stopped from __del__, so avoid
        # killing the process or removing the workspace twice.
        if not self.running:
            return
        os.kill(self.server_process.pid, signal.SIGTERM)
        self.server_process.wait()
        self.running = False
        self.devnull.close()
        shutil.rmtree(self.temp_workspace)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify CodeChecker store behavior."
    )
    parser.add_argument(
        "--name",
        default="unit_test_bazel",
        help="Project name to store the results under.",
    )
    # This argument is also found in the parse_check test
    # pylint: disable=duplicate-code
    parser.add_argument(
        "paths",
        nargs="+",
        help="Runfiles paths of the analysis target ($(rootpaths ...)); "
        "the report directory is selected from them.",
    )
    return parser.parse_args()


def check_store(report_dir: str, name: str, port: int, zip_loc: str) -> int:
    """Store the results and assert the store command succeeds."""
    ret, stdout, stderr = run_codechecker([
        "store",
        report_dir,
        "-n",
        name,
        f"--url=http://localhost:{port}/Default",
        "--zip-loc",
        zip_loc,
    ])
    if ret != 0:
        print(f"FAILED: CodeChecker store failed with exit code {ret}")
        print(f"stdout:\n{stdout}")
        print(f"stderr:\n{stderr}")
        return 1
    print("PASSED: CodeChecker store succeeded.")
    return 0


def main() -> int:
    """Entry point."""
    args = parse_args()
    report_dir = resolve_report_data(args.paths)
    exit_code = 1

    # CodeChecker store writes a compressed file while assembling its upload.
    # By default that goes into the report directory, which lives in the
    # read-only Bazel runfiles tree, so point --zip-loc at a writable dir.
    # NOTE: the --zip-loc flag is only available since CodeChecker 6.27.0.
    with tempfile.TemporaryDirectory() as zip_loc:
        server = CodeCheckerServer()
        try:
            exit_code = check_store(report_dir, args.name, server.port, zip_loc)
        finally:
            server.stop_codechecker_server()
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
