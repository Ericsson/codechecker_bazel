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
import sys
import unittest
import glob
from ..common.base import TestBase

BAZEL_BIN_DIR = os.path.join("../../..", "bazel-bin", "test", 
                                    "unit", "virtual_include")
BAZEL_TESTLOGS_DIR = os.path.join("../../..", "bazel-testlogs", "test", 
                                    "unit", "virtual_include")

class TestBasic(TestBase):
    """Basic tests"""

    def setUp(self):
        """Before every test: clean Bazel cache"""
        super().setUp()
        self.check_command("bazel clean")

    def test_bazel_plist_path_resolved(self):
        """Test: bazel build :codechecker_virtual_include"""
        self.check_command("bazel build //test/unit/virtual_include:codechecker_virtual_include", exit_code=0)
        self.check_command("bazel build //test/unit/virtual_include:code_checker_virtual_include", exit_code=0)
        plist_files = glob.glob(os.path.join(BAZEL_BIN_DIR, "**", "*.plist"), recursive=True)
        self.assertTrue(os.path.isdir(f"{BAZEL_BIN_DIR}/_virtual_includes"))
        for plist_file in plist_files:
            logging.debug(f"Checking file: {plist_file}")
            with open(plist_file, "r") as f: 
                content = f.read()
                if re.search(r"/_virtual_includes/", content):
                    self.fail(f"Found unresolved symlink within CodeChecker report: {plist_file}")

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
