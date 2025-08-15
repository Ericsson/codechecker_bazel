"""
TODO: Describe what this file does
"""
import os
import sys
import unittest
# Python path magic, necessary to avoid module errors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import TestBase

# TODO: fix folder name
WORKING_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
BAZEL_BIN_DIR = os.path.join("../../..", "bazel-bin", "test", 
                                    "unit", "my_test_folder")
BAZEL_TESTLOGS_DIR = os.path.join("../../..", "bazel-testlogs", "test", 
                                    "unit", "my_test_folder")

class TestTemplate(TestBase):
    """TODO: Add a description"""

    def setUp(self):
        """TODO: Define clean up before every test"""
        super().setUp()
        self.check_command("bazel clean")

    def test_template(self):
        """Test: TODO: describe your test"""
        self.fail("Test not implemented!")


if __name__ == "__main__":
    unittest.main(buffer=True) 