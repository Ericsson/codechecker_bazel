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
import shutil
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
        os.mkdir("tmp")
        shutil.copy("primary.cc", "tmp")
        shutil.copy("secondary.cc", "tmp")
        shutil.copy("linking.h", "tmp")
        shutil.copy("BUILD", "tmp")

    def tearDown(self):
        """Clean up working directory after every test"""
        super().tearDown()
        try:
            shutil.rmtree("tmp")
        except FileNotFoundError:
            self.fail("Temporary working directory does not exists!")

    def test_bazel_test_code_checker_caching(self):
        """
        Test whether bazel correctly uses cached analysis
        results for unchanged input files.
        """
        target = "//test/unit/caching/tmp:code_checker_caching"
        ret, _, _ = self.run_command(f"bazel build {target}")
        self.assertEqual(ret, 0)
        try:
            with open("tmp/secondary.cc", "a", encoding="utf-8") as f:
                f.write("//test")
        except FileNotFoundError:
            self.fail(f"File not found!")
        ret, _, stderr = self.run_command(f"bazel build {target} --subcommands")
        self.assertEqual(ret, 0)
        self.assertEqual(
            stderr.count(f"SUBCOMMAND: # {target} [action 'CodeChecker"), 1
        )

    def test_bazel_test_code_checker_ctu_caching(self):
        """
        Test whether bazel correctly reanalyses
        the whole project when CTU is enabled
        """
        target = "//test/unit/caching/tmp:code_checker_caching_ctu"
        ret, _, _ = self.run_command(f"bazel build {target}")
        self.assertEqual(ret, 0)
        try:
            with open("tmp/secondary.cc", "a", encoding="utf-8") as f:
                f.write("//test")
        except FileNotFoundError:
            self.fail(f"File not found!")
        ret, _, stderr = self.run_command(f"bazel build {target} --subcommands")
        self.assertEqual(ret, 0)
        # We expect both files to be reanalyzed, since there is no caching
        # implemented for CTU analysis
        self.assertEqual(
            stderr.count(f"SUBCOMMAND: # {target} [action 'CodeChecker"), 2
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
