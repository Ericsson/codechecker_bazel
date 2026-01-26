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
Test ruleset on open-source projects
"""
from pathlib import Path
import unittest
import os
from types import FunctionType
from common.base import TestBase
from common.tmpfile import TemporaryDir

ROOT_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/"
NOT_PROJECT_FOLDERS = ["templates", "__pycache__", ".pytest_cache"]


def get_test_dirs() -> list[str]:
    dirs = []
    for entry in os.listdir(ROOT_DIR):
        full_path = os.path.join(ROOT_DIR, entry)
        if os.path.isdir(full_path) and entry not in NOT_PROJECT_FOLDERS:
            dirs.append(entry)
    return dirs


PROJECT_DIRS = get_test_dirs()


# This will contain the generated tests.
class FOSSTestCollector(TestBase):
    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    # These are irrelevant for these kind of tests
    BAZEL_BIN_DIR = os.path.join("")
    BAZEL_TESTLOGS_DIR = os.path.join("")


# Creates test functions with the parameter: directory_name. Based on:
# https://eli.thegreenplace.net/2014/04/02/dynamically-generating-python-test-cases
def create_test_method(directory_name: str) -> FunctionType:
    """
    Returns a function pointer that points to a function for the given directory
    """

    def test_runner(self) -> None:
        project_root = os.path.join(ROOT_DIR, directory_name)

        self.assertTrue(
            os.path.exists(os.path.join(project_root, "init.sh")),
            f"Missing 'init.sh' in {directory_name}\n"
            + "Please consult with the README on how to add a new FOSS project",
        )
        with TemporaryDir() as project_working_dir:
            self.assertTrue(os.path.exists(project_working_dir))
            ret, _, _ = self.run_command(
                f"sh init.sh {project_working_dir}", project_root
            )
            module_file = Path(
                os.path.join(project_working_dir, "MODULE.bazel")
            )
            if os.path.exists(module_file):
                content = module_file.read_text().replace(
                    "{rule_path}",
                    f"{os.path.dirname(os.path.abspath(__file__))}/../../",
                )
                module_file.write_text(content)
            workspace_file = Path(
                os.path.join(project_working_dir, "WORKSPACE")
            )
            if os.path.exists(workspace_file):
                content = workspace_file.read_text().replace(
                    "{rule_path}",
                    f"{os.path.dirname(os.path.abspath(__file__))}/../../",
                )
                workspace_file.write_text(content)
            ret, _, _ = self.run_command(
                "bazel build :codechecker_test", project_working_dir
            )
            self.assertEqual(ret, 0)
            ret, _, _ = self.run_command(
                "bazel build :per_file_test", project_working_dir
            )
            self.assertEqual(ret, 0)

    return test_runner


# Dynamically add a test method for each project
# For each project directory it adds a new test function to the class
# This must be outside of the __main__ if, pytest doesn't run it that way
for dir_name in PROJECT_DIRS:
    test_name = f"test_{dir_name}"
    setattr(FOSSTestCollector, test_name, create_test_method(dir_name))

if __name__ == "__main__":
    unittest.main()
