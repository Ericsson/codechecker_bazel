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
Test wether CodeChecker parse and CodeChecker store
runs correctly on the produced report files
"""
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import unittest
from typing import Optional
from common.base import TestBase


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


class TestTemplate(TestBase):
    """Test CodeChecker parse, store"""

    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "parse"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "parse"
    )

    def test_parse_html(self):
        """Test: Parse results into html"""
        ret, _, _ = self.run_command(
            "bazel build //test/unit/parse:codechecker"
        )
        self.assertEqual(ret, 0)
        ret, out, _ = self.run_command(
            f"CodeChecker parse -e html {self.BAZEL_BIN_DIR}/codechecker/codechecker-files/data -o codecheckerHtml/"
        )
        self.assertEqual(ret, 2)  # Will exit with 2 because of bug being found
        shutil.rmtree("codecheckerHtml/")

    def test_store(self):
        """Test: Storing to CodeChecker server"""
        # FIXME: CodeChecker store wants to create a temporary folder inside
        # the report folder. Bazel's output folder however is readonly.
        # Adding the flag: "--experimental_writable_outputs"
        # makes the directory writeable
        ret, _, _ = self.run_command(
            "bazel build //test/unit/parse:codechecker --experimental_writable_outputs"
        )
        self.assertEqual(ret, 0)
        # Spin up a Codechecker server
        temp_workspace = tempfile.mkdtemp()
        server_command = [
            "CodeChecker",
            "server",
            "--workspace",
            temp_workspace,
            "--port",
            "8001",  # user running unittest must make this port free!
        ]
        devnull = open(os.devnull, "w")
        server_process = subprocess.Popen(server_command, stdout=devnull)
        self.assertTrue(wait_port(port=8001))
        ret, out, _ = self.run_command(
            f'CodeChecker store {self.BAZEL_BIN_DIR}/codechecker/codechecker-files/data -n "unit_test_bazel" --url=http://localhost:8001/Default'
        )
        os.kill(server_process.pid, signal.SIGTERM)
        server_process.wait()
        devnull.close()
        self.assertEqual(ret, 0)
        shutil.rmtree(temp_workspace)


if __name__ == "__main__":
    unittest.main(buffer=True)
