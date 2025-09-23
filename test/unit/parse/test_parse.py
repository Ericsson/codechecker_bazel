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
Test wether CodeChecker parse runs correctly on the produced report
"""
import os
import shutil
import unittest
from typing import final
from common.base import TestBase


class TestTemplate(TestBase):
    """TODO: Add a description"""

    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "parse"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "parse"
    )

    def tearDown(self):
        """Remove parse output folder after every test"""
        shutil.rmtree("codecheckerHtml/")
        return super().tearDown()

    def test_template(self):
        """Test: Parse results into html"""
        ret, _, _ = self.run_command(
            "bazel build //test/unit/parse:codechecker"
        )
        self.assertEqual(ret, 0)
        ret, out, _ = self.run_command(
            f"CodeChecker parse -e html {self.BAZEL_BIN_DIR}/codechecker/codechecker-files/data -o codecheckerHtml/"
        )
        self.assertEqual(ret, 2) # Will exit with 2 because of bug being found


if __name__ == "__main__":
    unittest.main(buffer=True)
