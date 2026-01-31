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
This file tests implementation_deps support
"""
import os
import unittest
from common.base import TestBase


class TestImplementationDeps(TestBase):
    """Test implementation_deps support"""

    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "implementation_deps"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "implementation_deps"
    )

    def test_codechecker_implementation_deps(self):
        """
        Test: bazel test --experimental_cc_implementation_deps
        //test/unit/implementation_deps:codechecker_implementation_deps
        """
        ret, _, _ = self.run_command(
            "bazel test --experimental_cc_implementation_deps "
            "//test/unit/implementation_deps:codechecker_implementation_deps"
        )
        self.assertEqual(ret, 3)
        test_log = os.path.join(
            self.BAZEL_TESTLOGS_DIR,  # type: ignore
            "codechecker_implementation_deps",
            "test.log",
        )
        self.assertTrue(
            self.contains_regex_in_file(test_log, r"core\.DivideZero")
        )
        self.assertTrue(
            self.contains_regex_in_file(test_log, r"cplusplus\.NewDeleteLeaks")
        )

    def test_per_file_implementation_deps(self):
        """
        Test: bazel test --experimental_cc_implementation_deps
        //test/unit/implementation_deps:pre_file_implementation_deps
        """
        ret, _, _ = self.run_command(
            "bazel test --experimental_cc_implementation_deps "
            "//test/unit/implementation_deps:per_file_implementation_deps"
        )
        self.assertEqual(ret, 3)
        test_log = os.path.join(
            self.BAZEL_TESTLOGS_DIR,  # type: ignore
            "per_file_implementation_deps",
            "test.log",
        )
        self.assertTrue(
            self.contains_regex_in_file(test_log, r"core\.DivideZero")
        )
        self.assertTrue(
            self.contains_regex_in_file(test_log, r"cplusplus\.NewDeleteLeaks")
        )

    def test_compile_commands_implementation_deps(self):
        """
        Test: bazel build --experimental_cc_implementation_deps
        //test/unit/implementation_deps:compile_commands_implementation_deps
        """
        ret, _, _ = self.run_command(
            "bazel build --experimental_cc_implementation_deps //test/unit/"
            "implementation_deps:compile_commands_implementation_deps"
        )
        self.assertEqual(ret, 0)
        compile_commands = os.path.join(
            self.BAZEL_BIN_DIR,  # type: ignore
            "compile_commands_implementation_deps",
            "compile_commands.json",
        )
        self.assertTrue(
            self.contains_regex_in_file(compile_commands, r"main.cpp")
        )
        self.assertTrue(
            self.contains_regex_in_file(compile_commands, r"dep.cpp")
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
