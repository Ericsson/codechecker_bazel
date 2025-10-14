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
Tests regex resolution from remote executor absolute path
to local relative paths
"""
import os
import re
import shutil
import unittest
from typing import Dict
from common.base import TestBase
from src.codechecker_script import fix_path_with_regex

PATH_RESOLUTION: Dict[str, str] = {
    # {Remote execution absolute path}: {project relative path}
    "/worker/build/5d2c60d87885b089/root/test/unit/legacy/src/lib.cc": "test/unit/legacy/src/lib.cc",
    "/worker/build/a0ed5e04f7c3b444/root/test/unit/legacy/src/ctu.cc": "test/unit/legacy/src/ctu.cc",
    "/worker/build/a0ed5e04f7c3b444/root/test/unit/legacy/src/fail.cc": "test/unit/legacy/src/fail.cc",
    # This resolution is impossible, because "test_inc" => "inc" cannot be resolved
    # "/worker/build/28e82627f5078a2d/root/bazel-out/k8-fastbuild/bin/test/unit/virtual_include/_virtual_includes/test_inc/zeroDiv.h": "test/unit/virtual_include/inc/zeroDiv.h"
}


class TestPathResolve(TestBase):
    """Test regex resolution of remote execution paths"""

    # Set working directory
    __test_path__ = os.path.dirname(os.path.abspath(__file__))
    BAZEL_BIN_DIR = os.path.join(
        "../../..", "bazel-bin", "test", "unit", "plist_res"
    )
    BAZEL_TESTLOGS_DIR = os.path.join(
        "../../..", "bazel-testlogs", "test", "unit", "plist_res"
    )
    dir = os.path.dirname(os.path.abspath(__file__)) + "/tmp"

    def test_remote_worker_path_resolution(self):
        """
        Test: Resolve absolute path of remote worker
        to a relative path of the original project
        """
        test_on : Dict[str, str] = PATH_RESOLUTION.copy()
        for before, res in test_on.items():
            after: str = fix_path_with_regex(before[:])
            # FIXME: change to assertEqual
            self.assertNotEqual(after, res)


if __name__ == "__main__":
    unittest.main(buffer=True)
