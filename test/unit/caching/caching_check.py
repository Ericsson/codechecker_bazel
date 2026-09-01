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
Generic caching verification script for Bazel py_test targets.

Verifies that Bazel correctly caches (or re-runs) CodeChecker analysis
actions when a source file is modified.

This script sets up a self-contained Bazel workspace in TEST_TMPDIR,
runs a build, modifies a source file, rebuilds with --subcommands,
and asserts on the number of CodeChecker actions that re-ran.

Usage:
    python caching_check.py \
        --target_name codechecker_caching \
        --file_to_modify secondary.cc \
        --expected_action_count 1
"""

import argparse
import os
import subprocess
import sys


MODULE_BAZEL_TEMPLATE = """\
module(name = "caching_test_workspace")

bazel_dep(name = "rules_cc", version = "0.2.3")
bazel_dep(name = "rules_python", version = "0.40.0")
bazel_dep(name = "rules_codechecker")
local_path_override(
    module_name = "rules_codechecker",
    path = "{rules_codechecker_path}",
)

python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(
    is_default = True,
    python_version = "3.12",
)
"""

BUILD_BAZEL = """\
load("@rules_cc//cc:defs.bzl", "cc_binary", "cc_library")
load("@rules_codechecker//:defs.bzl", "codechecker_test")

cc_library(
    name = "linking",
    hdrs = ["linking.h"],
)

cc_library(
    name = "secondary",
    srcs = ["secondary.cc"],
    deps = ["linking"],
)

cc_binary(
    name = "primary",
    srcs = ["primary.cc"],
    deps = [
        "linking",
        "secondary",
    ],
)

codechecker_test(
    name = "codechecker_caching",
    targets = ["primary"],
)

codechecker_test(
    name = "per_file_caching",
    per_file = True,
    targets = ["primary"],
)

codechecker_test(
    name = "per_file_caching_ctu",
    analyze = ["--ctu"],
    per_file = True,
    targets = ["primary"],
)
"""

LINKING_H = """\
#ifndef LINKING_H
#define LINKING_H
int foo();
#endif // LINKING_H
"""

PRIMARY_CC = """\
#include "linking.h"

int main(){
    return 1/foo();
}
"""

SECONDARY_CC = """\
#include "linking.h"

int foo(){
    return 1;
}
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify CodeChecker caching behavior."
    )
    parser.add_argument(
        "--target_name",
        required=True,
        help="Name of the codechecker_test target to build.",
    )
    parser.add_argument(
        "--file_to_modify",
        required=True,
        help="Source file to modify between builds.",
    )
    parser.add_argument(
        "--expected_action_count",
        type=int,
        required=True,
        help="Expected number of CodeChecker actions on rebuild.",
    )
    return parser.parse_args()


def run_bazel(cmd: str, cwd: str) -> tuple[int, str, str]:
    """Run a bazel command and return (exit_code, stdout, stderr)."""
    env = os.environ.copy()
    # Remove TEST_TMPDIR so the inner bazel doesn't inherit it
    # (otherwise it gets a 15s idle timeout and wrong output root)
    env.pop("TEST_TMPDIR", None)
    result = subprocess.run(
        cmd.split(),
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def find_rules_codechecker_path() -> str:
    """Find the real path to the rules_codechecker repository root.

    Follows runfiles symlinks to resolve the actual source location.
    """
    script_real_path = os.path.realpath(__file__)
    # Script is at <repo>/test/unit/caching/caching_check.py
    # so repo root is 3 levels up
    repo_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(script_real_path))
        )
    )
    if os.path.isfile(os.path.join(repo_root, "MODULE.bazel")):
        return repo_root
    print(f"FAILED: Cannot find rules_codechecker repo root")
    print(f"  script_real_path: {script_real_path}")
    print(f"  computed root: {repo_root}")
    sys.exit(1)


def write_file(path: str, content: str) -> None:
    """Write content to a file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def setup_workspace(target_dir: str,
                    rules_codechecker_path: str) -> None:
    """Write all workspace files into target_dir."""
    write_file(
        os.path.join(target_dir, "MODULE.bazel"),
        MODULE_BAZEL_TEMPLATE.format(
            rules_codechecker_path=rules_codechecker_path
        ),
    )
    write_file(os.path.join(target_dir, "BUILD.bazel"), BUILD_BAZEL)
    write_file(os.path.join(target_dir, "linking.h"), LINKING_H)
    write_file(os.path.join(target_dir, "primary.cc"), PRIMARY_CC)
    write_file(os.path.join(target_dir, "secondary.cc"), SECONDARY_CC)


def main() -> int:
    """Entry point."""
    args = parse_args()

    # Determine where to set up the inner workspace
    test_tmpdir = os.environ.get("TEST_TMPDIR")
    if not test_tmpdir:
        print("FAILED: TEST_TMPDIR not set (not running under bazel test?)")
        return 1

    inner_workspace = os.path.join(test_tmpdir, "workspace")
    os.makedirs(inner_workspace, exist_ok=True)

    # Find rules_codechecker repo root
    rules_codechecker_path = find_rules_codechecker_path()

    # Set up the inner workspace
    setup_workspace(inner_workspace, rules_codechecker_path)

    target = f"//:{args.target_name}"

    # First build: prime the cache
    ret, _, stderr = run_bazel(f"bazel build {target}", cwd=inner_workspace)
    if ret != 0:
        print(f"FAILED: First build failed with exit code {ret}")
        print(f"stderr: {stderr}")
        return 1

    # Modify the specified file
    file_path = os.path.join(inner_workspace, args.file_to_modify)
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write("//test")
    except FileNotFoundError:
        print(f"FAILED: File not found: {file_path}")
        return 1

    # Second build: check which actions re-run
    ret, _, stderr = run_bazel(
        f"bazel build {target} --subcommands", cwd=inner_workspace
    )
    if ret != 0:
        print(f"FAILED: Second build failed with exit code {ret}")
        print(f"stderr: {stderr}")
        return 1

    # Count CodeChecker actions in subcommands output
    search_pattern = (
        f"SUBCOMMAND: # {target} [action 'CodeChecker"
    )
    action_count = stderr.count(search_pattern)

    if action_count != args.expected_action_count:
        print(
            f"FAILED: Expected {args.expected_action_count} "
            f"CodeChecker action(s), got {action_count}"
        )
        print(f"Search pattern: {search_pattern}")
        print(f"stderr:\n{stderr}")
        return 1

    print(
        f"PASSED: Found {action_count} CodeChecker action(s) "
        f"as expected."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
