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
from typing import final
from common.base import TestBase


class TestCaching(TestBase):
    """Caching tests"""

    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "caching"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "caching"
    )

    @final
    @classmethod
    def setUpClass(cls):
        """Clean up before the test suite"""
        super().setUpClass()
        cls.run_command("bazel clean")

    def setUp(self):
        """Before every test: clean Bazel cache"""
        super().setUp()
        self.run_command("mkdir tmp")
        self.run_command("cp primary.cc secondary.cc linking.h BUILD tmp/")

    def tearDown(self):
        """Clean up working directory after every test"""
        super().tearDown()
        self.run_command("rm -rf tmp")

    def test_bazel_test_code_checker_caching(self):
        """Tests whether bazel uses cached output for unchanged files"""
        target = "//test/unit/caching/tmp:code_checker_caching"
        ret, _, _ = self.run_command(f"bazel build {target}")
        self.assertEqual(ret, 0)
        try:
            with open("tmp/secondary.cc", "a", encoding="utf-8") as f:
                f.write("//test")
        except FileNotFoundError:
            self.fail(f"File not found!")
        ret, stdout, stderr = self.run_command(
            f"bazel build {target} --subcommands"
        )
        self.assertEqual(ret, 0)
        content = stdout + stderr
        # FIXME: This should be 1
        self.assertEqual(
            content.count(f"SUBCOMMAND: # {target} [action 'CodeChecker"), 2
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
