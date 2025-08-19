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
TODO: Describe what this file does
"""
import os
import unittest
from typing import final
from common.base import TestBase


class TestTemplate(TestBase):
    """TODO: Add a description"""
    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    # TODO: fix folder name
    BAZEL_BIN_DIR = os.path.join("../../..", "bazel-bin", "test", 
                                        "unit", "my_test_folder")
    BAZEL_TESTLOGS_DIR = os.path.join("../../..", "bazel-testlogs", "test", 
                                        "unit", "my_test_folder")

    @final
    @classmethod
    def setUpClass(cls):
        """TODO: Define set up before the test suite"""
        super().setUpClass()
        cls.run_command("bazel clean")

    @final
    @classmethod
    def tearDownClass(cls):
        """TODO: Define clean up after the test suite"""
        super().tearDownClass()

    def setUp(self):
        """TODO: Define clean up before every test"""
        super().setUp()

    def tearDown(self):
        """TODO: Define clean up after every test"""
        return super().tearDown()

    def tearDown(self):
        """TODO: Define clean up after every test"""
        return super().tearDown()

    def test_template(self):
        """Test: TODO: describe your test"""
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main(buffer=True)
