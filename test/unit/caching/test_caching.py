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
Functional test, to check if caching is working correctly
"""
import unittest
import os
from common.base import TestBase


class TestCaching(TestBase):
    """Caching tests"""

    # This line is mandatory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))

    def setUp(self):
        """Before every test: clean Bazel cache"""
        super().setUp()
        self.check_command("bazel clean")

    def test_bazel_test_code_checker_caching(self):
        """Tests whether bazel uses cached output for unchanged files"""
        modified_file = "secondary.cc"
        target = "//test/unit/caching:code_checker_caching"
        self.check_command(
            f"cp {modified_file} {modified_file}.back", exit_code=0
        )
        self.check_command(f"bazel build {target}", exit_code=0)
        try:
            with open(f"{modified_file}", "a", encoding="utf-8") as f:
                f.write("//test")
        except FileNotFoundError:
            self.fail(f"File not found: {modified_file}")
        stdout, stderr = self.check_command(
            f"bazel build {target} --subcommands", exit_code=0
        )
        content = stdout + stderr
        self.check_command(
            f"mv {modified_file}.back {modified_file}", exit_code=0
        )
        self.assertEqual(content.count("SUBCOMMAND"), 1)


if __name__ == "__main__":
    unittest.main(buffer=True)
