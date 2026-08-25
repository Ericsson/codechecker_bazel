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
import logging
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

    # NOTE: Set by main()
    url = None
    target = None
    tests = []

    @classmethod
    def configure(cls, url, target, tests):
        """Initialize the class"""
        cls.url = url
        cls.target = target
        cls.tests = tests

    @classmethod
    def setUpClass(cls):
        """Download, extract, setup and analyze the FOSS project code"""
        if not cls.url:
            raise AssertionError("FOSS: project url is empty")
        if not cls.target:
            raise AssertionError("FOSS: bazel target is empty")
        if not cls.tests:
            raise AssertionError("FOSS: bazel test list is empty")

        cls.work_dir = Path(tempfile.mkdtemp())
        cls.output_base = cls.work_dir / ".bazel_output"

        # NOTE: Resolve rules_codechecker path from the script location
        cls.rules_path = Path(os.path.realpath(__file__)).parents[2]

        cls.download_and_extract()
        cls.setup_bazel_project()

        # NOTE: we run bazel build, not bazel test
        cls.build_result = cls.run_bazel(
            "build", *[f"//{t}" for t in cls.tests])

    @classmethod
    def tearDownClass(cls):
        """Stop bazel and cleanup"""
        if cls.work_dir.exists():
            cls.run_bazel("shutdown")
            # The outputs of bazel are read only
            subprocess.run(
                ["chmod", "-R", "u+w", str(cls.work_dir)],
                capture_output=True,
                check=False)
            shutil.rmtree(cls.work_dir, ignore_errors=True)

    @classmethod
    def download_and_extract(cls):
        """Download and extract FOSS project"""
        archive = cls.work_dir / "archive.tar.gz"
        # NOTE: using wget - it should be available in the system
        logging.debug("Downloading: %s", cls.url)
        subprocess.run(
            ["wget", "-q", "-O", str(archive), cls.url],
            check=True)
        logging.debug("Extracting: %s", archive)
        with tarfile.open(archive) as tar:
            members = tar.getmembers()
            prefix = members[0].name.split("/")[0]
            for member in members:
                member.name = member.name[len(prefix):].lstrip("/")
                if member.name:
                    tar.extract(member, cls.work_dir / "src")
        cls.project_dir = cls.work_dir / "src"
        logging.debug("Project: %s", cls.project_dir)

    @classmethod
    def build_file(cls):
        """The build file of the project, BUILD.bazel unless BUILD is used."""
        for name in ("BUILD.bazel", "BUILD"):
            build_file = cls.project_dir / name
            if build_file.exists():
                return build_file
        return cls.project_dir / "BUILD.bazel"

    @classmethod
    def setup_bazel_project(cls):
        """Append to MODULE.bazel and BUILD.bazel (or BUILD)"""
        with (cls.project_dir / "MODULE.bazel").open("a") as module_file:
            module_file.write(
                MODULE_TEMPLATE.format(rules_path=cls.rules_path))
        with cls.build_file().open("a") as build_file:
            build_file.write(
                BUILD_TEMPLATE.format(target=cls.target))

    @classmethod
    def run_bazel(cls, *arguments):
        """Run bazel in the project, return the completed process"""
        command = [
            "bazel", f"--output_base={cls.output_base}"] + list(arguments)
        logging.debug("Running: %s", " ".join(command))
        return subprocess.run(
            command,
            cwd=cls.project_dir,
            capture_output=True,
            check=False,
            text=True)

    def bazel_bin(self):
        """Return path to bazel-bin"""
        return Path(self.run_bazel("info", "bazel-bin").stdout.strip())

    def setUp(self):
        """Just indicate test start"""
        logging.debug("")
        logging.debug("." * 60)
        # NOTE: Earlier check if bazel build fails
        if self.build_result.returncode:
            logging.debug("Build failed! Skipping other tests")
            if self._testMethodName != "test_build_succeeds":
                self.skipTest("bazel build failed")

    def test_build_succeeds(self):
        """Verify that codechecker rules build successfully."""
        logging.debug("Build result: code = %d", self.build_result.returncode)
        logging.debug("stderr:\n%s", self.build_result.stderr)
        logging.debug("stdout:\n%s", self.build_result.stdout)
        self.assertEqual(self.build_result.returncode, 0,
                         f"bazel build failed:\n{self.build_result.stderr}")

    def test_build_artifacts(self):
        """Verify codechecker build artifacts."""
        def ls_la(directory):
            """List files in given directory"""
            result = subprocess.run(
                ["ls", "-la", str(directory) + "/"],
                cwd=self.project_dir,
                capture_output=True,
                check=False,
                text=True)
            logging.debug("-" * 20)
            logging.debug("ls -la %s:\n%s", directory, result.stdout)

        bazel_bin = self.bazel_bin()
        ls_la(bazel_bin)
        for test in self.tests:
            test = test.replace(":", "/").lstrip("/")
            logging.debug("test: %s", test)
            test_dir = bazel_bin / test
            ls_la(test_dir)
            self.assertTrue(test_dir.exists(),
                            f"test dir not found at {test_dir}")

    def test_compile_commands_output(self):
        """Verify compile_commands.json is valid and non-empty."""
        if ":compile_commands" not in self.tests:
            self.skipTest(f":compile_commands - not in tests ({self.tests})")
        bazel_bin = self.bazel_bin()
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

    def test_codechecker_test_outputs(self):
        """Verify codechecker produces expected output files."""
        if ":codechecker_test" not in self.tests:
            self.skipTest(f":codechecker_test - not in tests ({self.tests})")
        bazel_bin = self.bazel_bin()
        test_dir = bazel_bin / "codechecker_test"
        self.assertTrue(test_dir.exists(),
                        f"codechecker output dir not found at {test_dir}")
        cc_json = test_dir / "compile_commands.json"
        self.assertTrue(cc_json.exists(),
                        "codechecker: compile_commands.json not found")
        codechecker_log = test_dir / "codechecker.log"
        self.assertTrue(codechecker_log.exists(),
                        "codechecker: codechecker.log not found")
        log = codechecker_log.read_text()
        logging.debug("codechecker.log:\n%s", log)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--tests", nargs="+", required=True)
    args, remaining = parser.parse_known_args()

    # Enable debug logging
    if "-vvv" in remaining:
        logging.basicConfig(level=logging.DEBUG, format="[FOSS]: %(message)s")

    FossTest.configure(args.url, args.target, args.tests)

    unittest.main(argv=[sys.argv[0]] + remaining)
