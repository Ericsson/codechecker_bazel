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
import os
import json
import unittest
from common.base import TestBase

# The documentation for the build command can be found here:
# https://bazel.build/docs/user-manual#cconlyopt


class TestBasic(TestBase):
    """Basic tests"""

    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "compile_flags"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "compile_flags"
    )

    def test_bazel_test_compile_commands_filter(self):
        """Test: bazel test :compile_commands_filter"""
        build_cmd = (
            "bazel build "
            + "//test/unit/compile_flags:compile_commands_filter "
            + "--cxxopt=__CXX__ --conlyopt=__CONLY__"
        )
        exit_code, _, _ = self.run_command(build_cmd)
        self.assertEqual(0, exit_code)
        compile_commands = os.path.join(
            self.BAZEL_BIN_DIR,
            "compile_commands_filter",
            "compile_commands.json",
        )

        with open(compile_commands) as f:
            json_content = json.load(f)
            for source in json_content:
                if source["file"].endswith(".c"):
                    self.assertNotIn(
                        "__CXX__", source["command"], "C++ flag on C file!"
                    )
                    self.assertIn(
                        "__CONLY__",
                        source["command"],
                        "C only flag not on C file!",
                    )
                if source["file"].endswith(".cc"):
                    self.assertIn(
                        "__CXX__", source["command"], "C++ flag on C file!"
                    )
                    self.assertNotIn(
                        "__CONLY__",
                        source["command"],
                        "C only flag not on C file!",
                    )

    def test_bazel_test_code_checker_filter(self):
        """Test: bazel test :code_checker_filter"""
        build_cmd = (
            "bazel build "
            + "//test/unit/compile_flags:code_checker_filter "
            + "--cxxopt=__CXX__ --conlyopt=__CONLY__"
        )
        exit_code, _, _ = self.run_command(build_cmd)
        self.assertEqual(0, exit_code)
        compile_commands = os.path.join(
            self.BAZEL_BIN_DIR,
            "code_checker_filter",
            "data",
            "compile_commands.json",
        )
        self.assertTrue(os.path.exists(compile_commands))
        with open(compile_commands) as f:
            json_content = json.load(f)
            for source in json_content:
                if source["file"].endswith(".c"):
                    self.assertNotIn(
                        "__CXX__", source["command"], "C++ flag on C file!"
                    )
                    self.assertIn(
                        "__CONLY__",
                        source["command"],
                        "C only flag not on C file!",
                    )
                if source["file"].endswith(".cc"):
                    self.assertIn(
                        "__CXX__", source["command"], "C++ flag on C file!"
                    )
                    self.assertNotIn(
                        "__CONLY__",
                        source["command"],
                        "C only flag not on C file!",
                    )


if __name__ == "__main__":
    unittest.main(buffer=True)
