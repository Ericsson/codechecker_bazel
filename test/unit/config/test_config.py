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
Tests involving config files
"""
import os
import unittest
from common.base import TestBase


class TestConfig(TestBase):
    """Test whether config files are getting passed to CodeChecker correctly"""

    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "config"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "config"
    )

    def test_codechecker_json(self):
        """Test: bazel build //test/unit/config:codechecker_json"""
        ret, _, _ = self.run_command(
            "bazel build //test/unit/config:codechecker_json"
        )
        self.assertEqual(ret, 0)
        copied_config = os.path.join(
            self.BAZEL_BIN_DIR,  # type: ignore
            "codechecker_json",
            "config.json",
        )
        self.assertTrue(os.path.exists(copied_config))

    def test_codechecker_yaml(self):
        """Test: bazel build //test/unit/config:codechecker_yaml"""
        ret, _, _ = self.run_command(
            "bazel build //test/unit/config:codechecker_yaml"
        )
        self.assertEqual(ret, 0)
        copied_config = os.path.join(
            self.BAZEL_BIN_DIR,  # type: ignore
            "codechecker_yaml",
            "config.yaml",
        )
        self.assertTrue(os.path.exists(copied_config))

    def test_codechecker_test_json(self):
        """Test: bazel test //test/unit/config:codechecker_test_json"""
        ret, _, _ = self.run_command(
            "bazel test //test/unit/config:codechecker_test_json"
        )
        # Should not find the division by zero bug
        self.assertEqual(ret, 0)
        copied_config = os.path.join(
            self.BAZEL_BIN_DIR,  # type: ignore
            "codechecker_test_json",
            "config.json",
        )
        # After the fix the file name will change
        # from codechecker_config.json to config.json
        self.assertTrue(os.path.exists(copied_config))

    def test_codechecker_test_yaml(self):
        """Test: bazel test //test/unit/config:codechecker_test_yaml"""
        ret, _, _ = self.run_command(
            "bazel test //test/unit/config:codechecker_test_yaml"
        )
        # Should not find the division by zero bug
        self.assertEqual(ret, 0)
        copied_config = os.path.join(
            self.BAZEL_BIN_DIR,  # type: ignore
            "codechecker_test_yaml",
            "config.yaml",
        )
        self.assertTrue(os.path.exists(copied_config))

    def test_per_file_test_json(self):
        """Test: bazel test //test/unit/config:per_file_test_json"""
        ret, _, _ = self.run_command(
            "bazel test //test/unit/config:per_file_test_json"
        )
        # Should not find the division by zero bug
        self.assertEqual(ret, 0)
        copied_config = os.path.join(
            self.BAZEL_BIN_DIR,  # type: ignore
            "per_file_test_json",
            "config.json",
        )
        self.assertTrue(os.path.exists(copied_config))

    def test_per_file_test_yaml(self):
        """Test: bazel test //test/unit/config:per_file_test_yaml"""
        ret, _, _ = self.run_command(
            "bazel test //test/unit/config:per_file_test_yaml"
        )
        # Should not find the division by zero bug
        self.assertEqual(ret, 0)
        copied_config = os.path.join(
            self.BAZEL_BIN_DIR,  # type: ignore
            "per_file_test_yaml",
            "config.yaml",
        )
        self.assertTrue(os.path.exists(copied_config))


if __name__ == "__main__":
    unittest.main(buffer=True)
