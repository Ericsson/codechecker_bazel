# Copyright 2026 Ericsson AB
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
FOSS integration test runner for rules_codechecker.

Downloads a FOSS project, sets up a standalone Bazel project with
rules_codechecker, builds codechecker targets, and verifies outputs.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

MODULE_TEMPLATE = """
local_path_override(
    module_name = "rules_codechecker",
    path = "{rules_path}",
)
bazel_dep(name = "rules_codechecker")
"""

BUILD_TEMPLATE = """
load("@rules_codechecker//:defs.bzl", "codechecker_test", "compile_commands")

codechecker_test(
    name = "codechecker_test",
    targets = ["//{target}"],
)

codechecker_test(
    name = "codechecker_per_file",
    targets = ["//{target}"],
    per_file = True,
)

compile_commands(
    name = "compile_commands",
    targets = ["//{target}"],
)
"""


class FossTest(unittest.TestCase):
    """Base test that downloads a FOSS project and runs rules_codechecker."""

    # Set by main()
    url = None
    target = None
    tests = None

    def setUp(self):
        self.work_dir = Path(tempfile.mkdtemp())

        # Resolve rules_codechecker path from the real script location
        script_path = Path(os.path.realpath(__file__))
        self.rules_path = script_path.parent.parent.parent

        self._download_and_extract()
        self._setup_bazel_project()

    def tearDown(self):
        if self.work_dir.exists():
            subprocess.run(
                ["bazel", f"--output_base={self.work_dir / '.bazel_output'}",
                 "shutdown"],
                capture_output=True,
            )
            subprocess.run(
                ["chmod", "-R", "u+w", str(self.work_dir)],
                capture_output=True,
            )
            shutil.rmtree(self.work_dir, ignore_errors=True)

    def _download_and_extract(self):
        archive = self.work_dir / "archive.tar.gz"
        subprocess.run(
            ["wget", "-q", "-O", str(archive), self.url],
            check=True,
        )
        with tarfile.open(archive) as tar:
            members = tar.getmembers()
            prefix = members[0].name.split("/")[0]
            for m in members:
                m.name = m.name[len(prefix):].lstrip("/")
                if m.name:
                    tar.extract(m, self.work_dir / "src")
        self.project_dir = self.work_dir / "src"

    def _build_file(self):
        """The build file of the project, BUILD.bazel unless BUILD is used."""
        for name in ("BUILD.bazel", "BUILD"):
            build_file = self.project_dir / name
            if build_file.exists():
                return build_file
        return self.project_dir / "BUILD.bazel"

    def _setup_bazel_project(self):
        """Append to MODULE.bazel and BUILD.bazel (or BUILD)"""
        with (self.project_dir / "MODULE.bazel").open("a") as module_file:
            module_file.write(
                MODULE_TEMPLATE.format(rules_path=self.rules_path)
            )
        with self._build_file().open("a") as build_file:
            build_file.write(BUILD_TEMPLATE.format(target=self.target))

    def _bazel_build(self):
        targets = [f"//{t}" for t in self.tests]
        result = subprocess.run(
            ["bazel",
             f"--output_base={self.work_dir / '.bazel_output'}",
             "build"] + targets,
            cwd=self.project_dir,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0,
                         f"bazel build failed:\n{result.stderr}")

    def _bazel_bin(self):
        result = subprocess.run(
            ["bazel",
             f"--output_base={self.work_dir / '.bazel_output'}",
             "info", "bazel-bin"],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
        )
        return Path(result.stdout.strip())

    def test_build_succeeds(self):
        """Verify that codechecker rules build successfully."""
        self._bazel_build()

    def test_compile_commands_valid(self):
        """Verify compile_commands.json is valid and non-empty."""
        self._bazel_build()
        bazel_bin = self._bazel_bin()
        cc_json = bazel_bin / "compile_commands" / "compile_commands.json"
        self.assertTrue(cc_json.exists(),
                        f"compile_commands.json not found at {cc_json}")
        data = json.loads(cc_json.read_text())
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0,
                           "compile_commands.json is empty")
        for entry in data:
            self.assertIn("file", entry)
            self.assertIn("directory", entry)

    def test_codechecker_outputs_exist(self):
        """Verify codechecker produces expected output files."""
        self._bazel_build()
        bazel_bin = self._bazel_bin()
        cc_dir = bazel_bin / "codechecker_test"
        self.assertTrue(cc_dir.exists(),
                        f"codechecker output dir not found at {cc_dir}")
        cc_json = cc_dir / "compile_commands.json"
        self.assertTrue(cc_json.exists(),
                        "codechecker compile_commands.json not found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--tests", nargs="+", required=True)
    args, remaining = parser.parse_known_args()

    FossTest.url = args.url
    FossTest.target = args.target
    FossTest.tests = args.tests

    unittest.main(argv=[sys.argv[0]] + remaining)
