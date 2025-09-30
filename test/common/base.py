# Copyright 2023 Ericsson AB
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
Base for unit and functional tests
"""

import logging
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import unittest
import sys
from typing import Optional


# Based on:
# https://dev.to/farcellier/wait-for-a-server-to-respond-in-python-488e
def wait_port(
    port: int,
    host: str = "localhost",
    timeout: Optional[int] = 3000,
    attempt_every: int = 100,
) -> bool:
    """
    Wait until a port would be open,
    for example the port 8001 for CodeChecker server
    """
    start = time.monotonic()
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((host, port))
                s.close()
                return True
            except ConnectionRefusedError:
                if timeout is not None and time.monotonic() - start > (
                    timeout / 1000
                ):
                    return False

        time.sleep(attempt_every / 1000)


class TestBase(unittest.TestCase):
    """Unittest base abstract class"""

    # This variable must be overwritten in each subclass!
    __test_path__: Optional[str] = None
    BAZEL_BIN_DIR: Optional[str] = None
    BAZEL_TESTLOGS_DIR: Optional[str] = None

    @classmethod
    def setUpClass(cls):
        """Load module, save environment"""
        ErrorCollector: list[str] = []
        if cls.__test_path__ == None:
            ErrorCollector.append(
                "Test path must be overwritten! Use:"
                "\n__test_path__ = os.path.dirname(os.path.abspath(__file__))"
            )
        if cls.BAZEL_BIN_DIR == None:
            ErrorCollector.append(
                "Bazel bin directory must be overwritten! Use:"
                "../../../bazel-bin/test/unit/my_test_folder"
            )
        if cls.BAZEL_TESTLOGS_DIR == None:
            ErrorCollector.append(
                "Bazel test logs directory must be overwritten! Use:"
                "../../../bazel-testlogs/test/unit/my_test_folder"
            )
        if ErrorCollector:
            raise NotImplementedError("\n".join(ErrorCollector))
        # Enable debug logs for tests if "super verbose" flag is provided
        if "-vvv" in sys.argv:
            logging.basicConfig(
                level=logging.DEBUG, format="[TEST] %(levelname)5s: %(message)s"
            )
        # Move to test dir
        cls.test_dir = cls.__test_path__
        os.chdir(cls.test_dir)
        # Save environment and location
        cls.save_env = os.environ
        cls.save_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        """Restore environment"""
        os.chdir(cls.save_cwd)
        os.environ = cls.save_env
        try:
            assert cls.server_process.poll() != None, "Server not stopped"
        except AttributeError:
            pass  # if server_process is not set, everything is fine

    def setUp(self):
        """Before every test"""
        logging.debug("\n%s", "-" * 70)

    @classmethod
    def run_command(
        self, cmd: str, working_dir: Optional[str] = None
    ) -> tuple[int, str, str]:
        """
        Run shell command.
        returns:
        - exit code
        - stdout
        - stderr
        """
        logging.debug("Running: %s", cmd)
        commands = shlex.split(cmd)
        with subprocess.Popen(
            commands,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_dir,
        ) as process:
            stdout, stderr = process.communicate()
            return (
                process.returncode,
                f"stdout: {stdout.decode('utf-8')}",
                f"stderr: {stderr.decode('utf-8')}",
            )

    @classmethod
    def grep_file(cls, filename: str, regex: str):
        """
        Grep given filename.
        Returns list of matched lines.
        Returns empty list if no match is found
        """
        results: list[str] = []
        pattern = re.compile(regex)
        logging.debug("RegEx = r'%s'", regex)
        with open(filename, "r", encoding="utf-8") as fileobj:
            for line in fileobj:
                if pattern.search(line):
                    logging.debug(line)
                    results.append(line)
        return results

    @classmethod
    def contains_regex_in_file(cls, file_path: str, regex: str) -> bool:
        """
        Returns a boolean, whether the specified file contains the regex or not.
        """
        return cls.grep_file(file_path, regex) != []

    @classmethod
    def start_codechecker_server(cls):
        cls.temp_workspace = tempfile.mkdtemp()
        server_command = [
            "CodeChecker",
            "server",
            "--workspace",
            cls.temp_workspace,
            "--port",
            "8001",  # user running unittest must make this port free!
        ]
        cls.devnull = open(os.devnull, "w")
        cls.server_process: subprocess.Popen = subprocess.Popen(
            server_command, stdout=cls.devnull
        )
        assert wait_port(
            port=8001, timeout=10000
        ), "Failed to start CodeChecker server"

    @classmethod
    def stop_codechecker_server(cls):
        os.kill(cls.server_process.pid, signal.SIGTERM)
        cls.server_process.wait()
        cls.devnull.close()
        shutil.rmtree(cls.temp_workspace)

    def check_parsing(self, path, will_find_bug=True):
        ret, _, _ = self.run_command(f"CodeChecker parse {path}")
        self.assertEqual(ret, 2 if will_find_bug else 0)
