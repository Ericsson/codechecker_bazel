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
Test wether CodeChecker parse and CodeChecker store
runs correctly on the produced report files
"""
import os
import unittest
from typing import final
from common.base import TestBase


class TestTemplate(TestBase):
    """Test CodeChecker parse, store"""

    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "parse"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "parse"
    )

    @final
    @classmethod
    def setUpClass(cls):
        """Start CodeChecker server"""
        super().setUpClass()
        cls.start_codechecker_server()

    @final
    @classmethod
    def tearDownClass(cls):
        """Stop CodeChecker server"""
        cls.stop_codechecker_server()
        super().tearDownClass()

    def test_parse_html(self):
        """Test: Parse results into html"""
        ret, _, _ = self.run_command(
            "bazel build //test/unit/parse:codechecker"
        )
        self.assertEqual(ret, 0)
        self.check_parse(
            f"{self.BAZEL_BIN_DIR}/codechecker/codechecker-files/data"
        )

    def test_store(self):
        """Test: Storing to CodeChecker server"""
        # FIXME: CodeChecker store wants to create a temporary folder inside
        # the report folder. Bazel's output folder however is readonly.
        # Adding the flag: "--experimental_writable_outputs"
        # makes the directory writeable
        ret, _, _ = self.run_command(
            "bazel build //test/unit/parse:codechecker "
            "--experimental_writable_outputs"
        )
        self.assertEqual(ret, 0)
        self.check_store(
            f"{self.BAZEL_BIN_DIR}/codechecker/codechecker-files/data",
            "unit_test_bazel",
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
