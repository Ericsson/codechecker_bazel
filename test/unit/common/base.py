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
import subprocess
import unittest
import sys


class TestBase(unittest.TestCase):
    """Unittest base abstract class"""

    # This variable must be overwritten in each subclass!
    __test_path__: str = None
    BAZEL_BIN_DIR: str = None
    BAZEL_TESTLOGS_DIR: str = None

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
        # Enable debug logs for tests if "super verbose" flag is provided
        if "-vvv" in sys.argv:
            logging.basicConfig(
                level=logging.DEBUG,
                format="[TEST] %(levelname)5s: %(message)s")
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

    def setUp(self):
        """Before every test"""
        logging.debug("\n%s", "-" * 70)

    @classmethod
    def run_command(self, cmd: str, working_dir:str=None) -> tuple[int, str, str]:
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
    def grep_file(self, filename, regex):
        """
        Grep given filename.
        Returns list of matched lines.
        Returns empty list if no match is found
        """
        results : list[str] = []
        pattern = re.compile(regex)
        logging.debug("RegEx = r'%s'", regex)
        with open(filename, "r", encoding="utf-8") as fileobj:
            for line in fileobj:
                if pattern.search(line):
                    logging.debug(line)
                    results.append(line)
        return results
    
    @classmethod
    def contains_regex_in_file(self, file_path: str, regex: str) -> bool:
        """
        Returns a boolean, whether the specified file contains the regex or not.
        """
        return self.grep_file(file_path, regex) != []
