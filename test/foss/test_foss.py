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

import logging
import shlex
import subprocess
import sys
import unittest
import os

ROOT_DIR = "./"

NOT_PROJECT_FOLDERS = ["templates", "__pycache__", ".pytest_cache"]


def get_dynamic_test_dirs():
    dirs = []
    for entry in os.listdir(ROOT_DIR):
        full_path = os.path.join(ROOT_DIR, entry)
        if os.path.isdir(full_path) and entry not in NOT_PROJECT_FOLDERS:
            dirs.append(entry)
    return dirs


PROJECT_DIRS = get_dynamic_test_dirs()


# This will contain the generated tests.
class DynamicFOSSTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configure logging before running tests"""
        # Enable debug logs for tests if "super verbose" flag is provided
        if "-vvv" in sys.argv:
            logging.basicConfig(
                level=logging.DEBUG, format="[TEST] %(levelname)5s: %(message)s"
            )

    @classmethod
    def run_command(
        self, cmd: str, working_dir: str = None
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


# Dynamically add a test method for each project
for dir_name in PROJECT_DIRS:

    def create_test_method(directory_name):
        def test_runner(self):
            project_root = os.path.join(ROOT_DIR, directory_name)

            self.assertTrue(
                os.path.exists(os.path.join(project_root, "init.sh")),
                f"Missing 'init.sh' in {directory_name}",
            )
            project_working_dir = os.path.join(project_root, "test-proj")
            if not os.path.exists(project_working_dir):
                ret, _, _ = self.run_command("sh init.sh", project_root)
            self.assertTrue(os.path.exists(project_working_dir))
            ret, _, _ = self.run_command(
                "bazel build :codechecker_test", project_working_dir
            )
            self.assertEqual(ret, 0)
            ret, _, _ = self.run_command(
                "bazel build :code_checker_test", project_working_dir
            )
            self.assertEqual(ret, 0)

        return test_runner

    test_name = f"test_{dir_name}"
    setattr(DynamicFOSSTest, test_name, create_test_method(dir_name))

if __name__ == "__main__":
    unittest.main()
