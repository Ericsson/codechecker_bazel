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
Test external repositories with codechecker
"""
from logging import debug
import logging
import os
import shutil
import unittest
from typing import final
from common.base import TestBase


class TestImplDepExternalDep(TestBase):
    """Test external repositories with codechecker"""
    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join("bazel-bin")
    BAZEL_TESTLOGS_DIR = os.path.join("bazel-testlogs")

    @final
    @classmethod
    def setUpClass(cls):
        """
        Copy bazelversion from main, otherwise bazelisk will download the latest
        bazel version.
        """
        super().setUpClass()
        try:
            shutil.copy("../../../.bazelversion", ".bazelversion")
            shutil.copy(
                "../../../.bazelversion", "third_party/my_lib/.bazelversion")
        except:
            logging.debug("No bazel version set, using system default")

    @final
    @classmethod
    def tearDownClass(cls):
        """Remove bazelversion from this test"""
        super().tearDownClass()
        try:
            os.remove(".bazelversion")
        except:
            pass
        try:
            os.remove("third_party/my_lib/.bazelversion")
        except:
            pass

    def test_compile_commands_external_lib(self):
        """Test: bazel build :compile_commands_isystem"""
        ret, _, _ = self.run_command(
            "bazel build :compile_commands_isystem")
        self.assertEqual(ret, 0)
        comp_json_file = os.path.join(
            self.BAZEL_BIN_DIR, # pyright: ignore[reportOptionalOperand]
            "compile_commands_isystem",
            "compile_commands.json")

        # TODO: Set to True, should find external lib as an -isystem include
        self.assertFalse(self.contains_regex_in_file(
            comp_json_file,
            "-isystem external/external_lib/include"))
        self.assertFalse(self.contains_regex_in_file(
            comp_json_file,
            "-isystem " +
            "bazel-out/k8-fastbuild/bin/external/external_lib/include"))

    def test_codechecker_external_lib(self):
        """Test: bazel build :odechecker_external_deps"""
        ret, _, _ = self.run_command(
            "bazel build :codechecker_external_deps")
        # TODO: set to 1, the nothing header should be found
        self.assertEqual(ret, 1)

    def test_per_file_external_lib(self):
        """Test: bazel build :per_file_external_deps"""
        ret, _, _ = self.run_command(
            "bazel build :per_file_external_deps")
        # TODO: set to 1, the nothing header should be found
        self.assertEqual(ret, 1)


if __name__ == "__main__":
    unittest.main(buffer=True)
