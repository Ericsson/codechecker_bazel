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
Unit and functional tests
"""
import logging
import os
import re
import shlex
import subprocess
import sys
from time import sleep
import unittest


class TestBase(unittest.TestCase):
    """Unittest base abstract class"""

    BAZEL_BIN_DIR = os.path.join("../../..", "bazel-bin", "test",
                                    "unit", "caching")
    BAZEL_TESTLOGS_DIR = os.path.join("../../..", "bazel-testlogs", "test",
                                    "unit", "caching")

    @classmethod
    def setUpClass(cls):
        """Load module, save environment"""
        # Save environment and location
        cls.save_env = os.environ
        cls.save_cwd = os.getcwd()
        # Move to test dir
        cls.test_dir = os.path.abspath(os.path.dirname(__file__))
        os.chdir(cls.test_dir)

    @classmethod
    def tearDownClass(cls):
        """Restore environment"""
        os.chdir(cls.save_cwd)
        os.environ = cls.save_env

    def setUp(self):
        """Before every test"""
        logging.debug("\n%s", "-" * 70)

    def check_command(self, cmd, exit_code=0):
        """Run shell command and check status"""
        logging.debug("Running: %s", cmd)
        commands = shlex.split(cmd)
        with subprocess.Popen(commands,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE) as process:
            stdout, stderr = process.communicate()
            self.assertEqual(
                process.returncode,
                exit_code, "\n" + "\n".join([
                    f"command: {cmd}",
                    f"stdout: {stdout.decode('utf-8')}",
                    f"stderr: {stderr.decode('utf-8')}"]))
            return "\n".join([
                    f"command: {cmd}",
                    f"stdout: {stdout.decode('utf-8')}",
                    f"stderr: {stderr.decode('utf-8')}"])

    def grep_file(self, filename, regex):
        """Grep given filename"""
        pattern = re.compile(regex)
        logging.debug("RegEx = r'%s'", regex)
        with open(filename, "r", encoding="utf-8") as fileobj:
            for line in fileobj:
                if pattern.search(line):
                    logging.debug(line)
                    return line
        self.fail(f"Could not find r'{regex}' in '{filename}'")
        return ""

class TestBasic(TestBase):
    """Basic tests"""

    def setUp(self):
        """Before every test: clean Bazel cache"""
        super().setUp()
        self.check_command("bazel clean")

    def test_bazel_test_code_checker_caching(self):
        """Tests whether bazel uses cached output for unchanged files"""
        modified_file = "secondary.cc"
        target = "//test/unit/caching:code_checker_caching"
        self.check_command(f"cp {modified_file} {modified_file}.back", exit_code=0)
        self.check_command(f"bazel build {target}", exit_code=0)
        try:
            with open(modified_file, 'a', encoding='utf-8') as f:
                f.write("//test")
        except FileNotFoundError:
            self.fail(f"File not found: {modified_file}")
        content = self.check_command(f"bazel build {target} --subcommands", exit_code=0)
        self.check_command(f"mv {modified_file}.back {modified_file}", exit_code=0)
        self.assertEqual(content.count("SUBCOMMAND"),1)


def setup_logging():
    """Setup logging level for test execution"""
    # Enable debug logs for tests if "super verbose" flag is provided
    if "-vvv" in sys.argv:
        logging.basicConfig(
            level=logging.DEBUG,
            format="[TEST] %(levelname)5s: %(message)s")


def main():
    """Run unittest"""
    setup_logging()
    logging.debug("Start testing...")
    unittest.main(buffer=True)


if __name__ == "__main__":
    main()
