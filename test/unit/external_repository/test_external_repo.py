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
    BAZEL_VERSION = None

    @final
    @classmethod
    def setUpClass(cls):
        """
        Copy bazelversion from main, otherwise bazelisk will download the latest
        bazel version.
        """
        # The folder bazel-external_repository contains this script
        # and the unittest test discovery finds it.
        # This is why, it is imperative that these directories get cleared
        cls.run_command("bazel clean")
        super().setUpClass()
        try:
            shutil.copy("../../../.bazelversion", ".bazelversion")
            shutil.copy(
                "../../../.bazelversion", "third_party/my_lib/.bazelversion")

        except:
            logging.debug("No bazel version set, using system default")
        _, stdout, _ = cls.run_command("bazel --version")
        cls.BAZEL_VERSION = stdout.split(' ')[2].strip()
        logging.debug("Using Bazel", cls.BAZEL_VERSION)

    @final
    @classmethod
    def tearDownClass(cls):
        """Remove bazelversion from this test"""
        super().tearDownClass()
        # The folder bazel-external_repository contains this script
        # and the unittest test discovery finds it.
        # This is why, it is imperative that these directories get cleared
        cls.run_command("bazel clean")
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
        comp_json_file = os.path.join( # pyright: ignore
            self.BAZEL_BIN_DIR, # pyright: ignore
            "compile_commands_isystem",
            "compile_commands.json")

        # The ~override part is a consquence of using Bzlmod.
        if self.BAZEL_VERSION.startswith("6"): # type: ignore
            pattern1 = "-isystem external/external_lib~override/include"
            pattern2 = "-isystem " + \
            "bazel-out/k8-fastbuild/bin/external/external_lib~override/include"
        elif self.BAZEL_VERSION.startswith("7"): # type: ignore
            pattern1 = "-isystem external/external_lib~/include"
            pattern2 = "-isystem " + \
            "bazel-out/k8-fastbuild/bin/external/external_lib~/include"
        else: # Bazel 8
            pattern1 = r"-isystem external/external_lib\+/include"
            pattern2 = r"-isystem " + \
            r"bazel-out/k8-fastbuild/bin/external/external_lib\+/include"

        self.assertTrue(self.contains_regex_in_file(
            comp_json_file,
            pattern1))
        self.assertTrue(self.contains_regex_in_file(
            comp_json_file,
            pattern2))

    def test_codechecker_external_lib(self):
        """Test: bazel build :codechecker_external_deps"""
        ret, _, _ = self.run_command(
            "bazel build :codechecker_external_deps")
        self.assertEqual(ret, 0)

    def test_per_file_external_lib(self):
        """Test: bazel build :per_file_external_deps"""
        ret, _, _ = self.run_command(
            "bazel build :per_file_external_deps")
        # TODO: set to 1, the nothing header should be found
        self.assertEqual(ret, 1)


if __name__ == "__main__":
    unittest.main(buffer=True)
