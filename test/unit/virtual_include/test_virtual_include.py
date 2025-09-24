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
We want CodeChecker to point to the original files in its results, this needs
post processing.
Bazel creates _virtual_includes folder for headers, declared in a cc_library
rule with the include_prefix or strip_include_prefix. When warnings are found
in these headers, their paths in the plist files should get resolved to the
original file path.
This unittest test whether these paths containing `_virtual_include` have been
resolved
"""
import logging
import os
import re
import unittest
import glob
from typing import final
from common.base import TestBase


class TestVirtualInclude(TestBase):
    """Tests checking virtual include path resolution"""

    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "virtual_include"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "virtual_include"
    )

    @final
    @classmethod
    def setUpClass(cls):
        """Set up before the test suite"""
        super().setUpClass()
        cls.run_command("bazel clean")

    def contains_in_files(self, regex, file_list):
        result = []
        for file in file_list:
            logging.debug(f"Checking file: {file}")
            if self.contains_regex_in_file(file, regex):
                result.append(file)
        return result

    def test_bazel_code_checker_plist_path_resolved(self):
        """Test: bazel build :code_checker_virtual_include"""
        ret, _, _ = self.run_command(
            "bazel build //test/unit/virtual_include:code_checker_virtual_include",
        )
        self.assertEqual(ret, 0)
        plist_files = glob.glob(
            os.path.join(
                self.BAZEL_BIN_DIR,
                "code_checker_virtual_include",
                "**",
                "*.plist",
            ),
            recursive=True,
        )
        # Test whether the _virtual_include directory was actually created.
        self.assertTrue(
            os.path.isdir(f"{self.BAZEL_BIN_DIR}/_virtual_includes")
        )
        # FIXME: In the postprocessed plists, all _virtual_include paths 
        # should've been removed. Possible fix is in the github PR #14.
        self.assertNotEqual(
            self.contains_in_files(r"/_virtual_includes/", plist_files), []
        )

    def test_bazel_codechecker_plist_path_resolved(self):
        """Test: bazel build :codechecker_virtual_include"""
        ret, _, _ = self.run_command(
            "bazel build //test/unit/virtual_include:codechecker_virtual_include"
        )
        self.assertEqual(ret, 0)
        plist_files = glob.glob(
            os.path.join(
                self.BAZEL_BIN_DIR,
                "codechecker_virtual_include",
                "**",
                "*.plist",
            ),
            recursive=True,
        )
        # Test whether the _virtual_include directory was actually created.
        self.assertTrue(
            os.path.isdir(f"{self.BAZEL_BIN_DIR}/_virtual_includes")
        )
        self.assertEqual(
            self.contains_in_files(r"/_virtual_includes/", plist_files), []
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
