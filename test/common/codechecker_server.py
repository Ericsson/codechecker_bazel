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
Codechecker server functionality, and related functions
"""

import os
import shutil
import signal
import socket
import subprocess
import tempfile
import time


# Based on:
# https://dev.to/farcellier/wait-for-a-server-to-respond-in-python-488e
def wait_port(
    port: int,
    host: str = "localhost",
    timeout: int = 3000,
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


class CodeCheckerServer:
    """
    CodeCheckerServer object for testing.
    Cleans up after itself.
    """
    def __init__(self, port="8001"):
        self.running = False
        self.port = port
        self.temp_workspace = tempfile.mkdtemp()
        self.start_codechecker_server()

    def __del__(self):
        self.stop_codechecker_server()

    def start_codechecker_server(self):
        """
        Starts a CodeChecker server instance on port 8001
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
            self.port,
        ]
        # These file/popen processes are closed when the object dies
        # pylint: disable=consider-using-with
        self.devnull = open(os.devnull, "w", encoding="utf-8")
        # pylint: disable=consider-using-with
        self.server_process: subprocess.Popen = subprocess.Popen(
            server_command, stdout=self.devnull
        )
        assert wait_port(
            port=8001, timeout=10000
        ), "Failed to start CodeChecker server"
        self.running = True

    def stop_codechecker_server(self):
        """
        Stops the CodeChecker server started by start_codechecker_server
        """
        os.kill(self.server_process.pid, signal.SIGTERM)
        self.server_process.wait()
        self.running = False
        self.devnull.close()
        shutil.rmtree(self.temp_workspace)
