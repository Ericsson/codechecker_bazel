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
Checks whether analysis runs on generated files too
"""
import os
import unittest
from common.base import TestBase


class TestGeneratedFiles(TestBase):
    """Tests involving generated header and source files"""

    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "generated_files"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "generated_files"
    )

    def test_genrule_header_codechecker(self):
        """
        Test: bazel test //test/unit/generated_files:codechecker_genrule_header
        """
        ret, _, _ = self.run_command(
            "bazel test //test/unit/generated_files:codechecker_genrule_header"
        )
        self.assertEqual(ret, 3)
        test_log = os.path.join(
            self.BAZEL_TESTLOGS_DIR,  # type: ignore
            "codechecker_genrule_header",
            "test.log",
        )
        self.assertTrue(os.path.exists(test_log))
        self.assertTrue(
            self.contains_regex_in_file(
                test_log, r"defect\(s\) in genrule_header.h"
            )
        )

    def test_genrule_source_codechecker(self):
        """
        Test: bazel test //test/unit/generated_files:codechecker_genrule_source
        """
        ret, _, _ = self.run_command(
            "bazel test //test/unit/generated_files:codechecker_genrule_source"
        )
        self.assertEqual(ret, 3)
        test_log = os.path.join(
            self.BAZEL_TESTLOGS_DIR,  # type: ignore
            "codechecker_genrule_source",
            "test.log",
        )
        self.assertTrue(os.path.exists(test_log))
        self.assertTrue(
            self.contains_regex_in_file(
                test_log, r"defect\(s\) in genrule_source.cc"
            )
        )

    def test_genrule_header_per_file(self):
        """
        Test: bazel test //test/unit/generated_files:per_file_genrule_header
        """
        ret, _, _ = self.run_command(
            "bazel test //test/unit/generated_files:per_file_genrule_header"
        )
        self.assertEqual(ret, 3)
        test_log = os.path.join(
            self.BAZEL_TESTLOGS_DIR,  # type: ignore
            "per_file_genrule_header",
            "test.log",
        )
        self.assertTrue(os.path.exists(test_log))
        self.assertTrue(
            self.contains_regex_in_file(
                test_log, r"defect\(s\) in genrule_header.h"
            )
        )

    def test_genrule_source_per_file(self):
        """
        Test: bazel test //test/unit/generated_files:per_file_genrule_source
        """
        ret, _, _ = self.run_command(
            "bazel test //test/unit/generated_files:per_file_genrule_source"
        )
        self.assertEqual(ret, 3)
        test_log = os.path.join(
            self.BAZEL_TESTLOGS_DIR,  # type: ignore
            "per_file_genrule_source",
            "test.log",
        )
        self.assertTrue(os.path.exists(test_log))
        self.assertTrue(
            self.contains_regex_in_file(
                test_log, r"defect\(s\) in genrule_source.cc"
            )
        )

    def test_genrule_source_compile_commands(self):
        """
        Test:
        bazel build //test/unit/generated_files:compile_commands_genrule_source
        """
        target = "genrule_source"
        ret, _, _ = self.run_command(
            "bazel build "
            + f"//test/unit/generated_files:compile_commands_{target}"
        )
        self.assertEqual(ret, 0)
        compile_commands = os.path.join(
            self.BAZEL_BIN_DIR,  # type: ignore
            f"compile_commands_{target}",
            "compile_commands.json",
        )
        self.assertTrue(os.path.exists(compile_commands))
        self.assertTrue(
            self.contains_regex_in_file(
                compile_commands, rf"\"file\":.*{target}.cc"
            )
        )

    def test_genrule_header_compile_commands(self):
        """
        Test:
        bazel build //test/unit/generated_files:compile_commands_genrule_header
        """
        target = "genrule_header"
        ret, _, _ = self.run_command(
            "bazel build "
            + f"//test/unit/generated_files:compile_commands_{target}"
        )
        self.assertEqual(ret, 0)
        compile_commands = os.path.join(
            self.BAZEL_BIN_DIR,  # type: ignore
            f"compile_commands_{target}",
            "compile_commands.json",
        )
        self.assertTrue(os.path.exists(compile_commands))
        self.assertTrue(
            self.contains_regex_in_file(
                compile_commands, rf"\"file\":.*{target}_consumer.cc"
            )
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
