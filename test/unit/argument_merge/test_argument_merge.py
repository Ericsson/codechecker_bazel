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
Tests wether default argument options and
user given arguments are merged correctly
"""
import os
import re
import unittest
from common.base import TestBase


class TestTemplate(TestBase):
    """Argument merging Tests"""

    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "argument_merge"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "argument_merge"
    )

    def test_per_file_argument_merge(self):
        """Test: Whether default options gets override"""
        code, _, _ = self.run_command(
            "bazel build //test/unit/argument_merge:per_file_argument_merge"
        )
        self.assertEqual(code, 0)
        matched_lines: list[str] = self.grep_file(
            self.BAZEL_BIN_DIR
            + "/per_file_argument_merge/data/"
            + "test-unit-argument_merge-main.cc_codechecker.log",
            r"--analyzers",
        )
        self.assertEqual(len(re.findall("--analyzers", matched_lines[0])), 1)


if __name__ == "__main__":
    unittest.main(buffer=True)
