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
import logging
import os
import re
import shutil
import tempfile
import unittest
from typing import final
from common.base import TestBase
from pathlib import Path



class TestImplDepExternalDep(TestBase):
    """Test external repositories with codechecker"""
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
        # Set working directory before calling base class!
        cls.__test_path__ = tempfile.mkdtemp()
        try:
            shutil.copytree(
                os.path.dirname(os.path.abspath(__file__)),
                cls.__test_path__,
                dirs_exist_ok=True
            )
            module_file = Path(os.path.join(cls.__test_path__, "MODULE.bazel"))
            content = module_file.read_text().replace(
                "../../../",
                f"{os.path.dirname(os.path.abspath(__file__))}/../../../"
                )
            module_file.write_text(content)
            workspace_file = Path(os.path.join(cls.__test_path__, "WORKSPACE"))
            content = workspace_file.read_text().replace(
                "../../../",
                f"{os.path.dirname(os.path.abspath(__file__))}/../../../"
                )
            workspace_file.write_text(content)
        except Exception as e:
            raise Exception(f"Failed to copy files to the temporary folder {e}")
        try:
            shutil.copy(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "../../../",
                    ".bazelversion",
                ),
                os.path.join(cls.__test_path__, ".bazelversion")
            )
        except:
            logging.debug("No bazel version set, using system default")
        _, version, _ = cls.run_command("bazel --version")
        cls.BAZEL_VERSION = re.sub(r".*bazel ", "", version)
        logging.debug(f"System default is: {cls.BAZEL_VERSION}")
        super().setUpClass()

    @final
    @classmethod
    def tearDownClass(cls):
        """Remove bazelversion from this test"""
        super().tearDownClass()
        try:
            os.remove(cls.__test_path__)  #type: ignore
        except:
            pass

    def test_compile_commands_external_lib(self):
        """Test: bazel build :compile_commands_isystem --experimental_cc_implementation_deps"""
        ret, _, _ = self.run_command(
            "bazel build :compile_commands_isystem --experimental_cc_implementation_deps")
        self.assertEqual(ret, 0)
        comp_json_file = os.path.join(
            self.BAZEL_BIN_DIR, # pyright: ignore[reportOptionalOperand]
            "compile_commands_isystem",
            "compile_commands.json")

        # The ~override part is a consequence of using Bzlmod.
        if self.BAZEL_VERSION.startswith("6"): # type: ignore
            pattern1 = "-isystem external/external_lib~override/include"
            pattern2 = "-isystem " + \
            "bazel-out/k8-fastbuild/bin/external/external_lib~override/include"
        else:
            pattern1 = "-isystem external/external_lib~/include"
            pattern2 = "-isystem " + \
            "bazel-out/k8-fastbuild/bin/external/external_lib~/include"

        self.assertTrue(self.contains_regex_in_file(
            comp_json_file,
            pattern1))
        self.assertTrue(self.contains_regex_in_file(
            comp_json_file,
            pattern2))

    def test_codechecker_external_lib(self):
        """Test: bazel build :codechecker_external_deps --experimental_cc_implementation_deps"""
        ret, _, _ = self.run_command(
            "bazel build :codechecker_external_deps --experimental_cc_implementation_deps")
        self.assertEqual(ret, 0)

    def test_per_file_external_lib(self):
        """Test: bazel build :per_file_external_deps --experimental_cc_implementation_deps"""
        ret, _, _ = self.run_command(
            "bazel build :per_file_external_deps --experimental_cc_implementation_deps")
        # TODO: set to 1, the nothing header should be found
        self.assertEqual(ret, 1)


if __name__ == "__main__":
    unittest.main(buffer=True)
