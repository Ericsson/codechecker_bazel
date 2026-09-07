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
Test runner for external repository tests.

This script creates a temporary Bazel workspace, copies source files into it,
runs a bazel command, and asserts on the result. It is designed to be invoked
by the external_test() Bazel macro.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

MODULE_BAZEL_CONTENT = """\
\"\"\"Test workspace for external repository integration test.\"\"\"

local_path_override(
    module_name = "rules_codechecker",
    path = "{repo_root}",
)

bazel_dep(name = "rules_codechecker")

local_path_override(
    module_name = "external_lib",
    path = "third_party/my_lib",
)

bazel_dep(name = "external_lib")
bazel_dep(name = "rules_cc", version = "0.2.17")
"""

BUILD_CONTENT = """\
load("@rules_cc//cc:defs.bzl", "cc_binary", "cc_library")
load(
    "@rules_codechecker//:defs.bzl",
    "codechecker_test",
    "compile_commands",
)

cc_library(
    name = "intermediate_lib",
    srcs = ["intermediate.cpp"],
    hdrs = ["intermediate.h"],
    implementation_deps = ["@external_lib//:lib"],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "isystem_impl_dep",
    srcs = ["main.cc"],
    deps = [":intermediate_lib"],
)

compile_commands(
    name = "compile_commands_isystem",
    targets = [":isystem_impl_dep"],
)

codechecker_test(
    name = "codechecker_external_deps",
    tags = ["manual"],
    targets = ["isystem_impl_dep"],
)

codechecker_test(
    name = "per_file_external_deps",
    per_file = True,
    tags = ["manual"],
    targets = ["isystem_impl_dep"],
)
"""

THIRD_PARTY_BUILD_CONTENT = """\
load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "lib",
    hdrs = ["include/nothing.h"],
    includes = ["include"],
    visibility = ["//visibility:public"],
)
"""

THIRD_PARTY_MODULE_CONTENT = """\
module(name = "external_lib")

bazel_dep(name = "rules_cc", version = "0.2.17")
"""

THIRD_PARTY_HEADER_CONTENT = """\
#pragma once
// Just a dummy header
"""


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a bazel command in a generated workspace"
    )
    parser.add_argument(
        "--repo_root",
        required=True,
        help="Path to a file in the repo root (MODULE.bazel)",
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["build", "test"],
        help="Bazel action to run",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Bazel target (e.g. ':codechecker_external_deps')",
    )
    parser.add_argument(
        "extra_flags",
        nargs="*",
        default=[],
        help="Extra flags to pass to bazel (after --)",
    )
    parser.add_argument(
        "--expected_exit_code",
        type=int,
        default=0,
        help="Expected exit code from the bazel command",
    )
    parser.add_argument(
        "--output_file",
        help="Relative path to output file to check (from workspace)",
    )
    parser.add_argument(
        "--contains",
        nargs="*",
        default=[],
        help="Regex patterns that must appear in the output file",
    )
    parser.add_argument(
        "--srcs",
        nargs="*",
        default=[],
        help="Source files to copy into the workspace root",
    )
    return parser.parse_args()


def resolve_repo_root(module_bazel_path):
    """Resolve the repo root from the MODULE.bazel runfiles path."""
    resolved = os.path.realpath(module_bazel_path)
    return os.path.dirname(resolved)


def copy_file(src, dst):
    """Copy a file, creating parent directories as needed."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def write_file(path, content):
    """Write content to a file, creating parent directories."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def setup_workspace(tmpdir, repo_root, srcs):
    """Set up the temporary workspace with all needed files."""
    # Write MODULE.bazel
    module_content = MODULE_BAZEL_CONTENT.format(repo_root=repo_root)
    write_file(os.path.join(tmpdir, "MODULE.bazel"), module_content)

    # Write empty WORKSPACE
    write_file(
        os.path.join(tmpdir, "WORKSPACE"),
        "# This file is mandatory for old Bazel versions\n",
    )

    # Write BUILD
    write_file(os.path.join(tmpdir, "BUILD"), BUILD_CONTENT)

    # Copy source files into workspace root
    for src_path in srcs:
        real_src = os.path.realpath(src_path)
        basename = os.path.basename(real_src)
        copy_file(real_src, os.path.join(tmpdir, basename))

    # Write third_party/my_lib files
    tp_dir = os.path.join(tmpdir, "third_party", "my_lib")
    write_file(
        os.path.join(tp_dir, "BUILD"), THIRD_PARTY_BUILD_CONTENT
    )
    write_file(
        os.path.join(tp_dir, "MODULE.bazel"),
        THIRD_PARTY_MODULE_CONTENT,
    )
    write_file(
        os.path.join(tp_dir, "include", "nothing.h"),
        THIRD_PARTY_HEADER_CONTENT,
    )

    # Copy .bazelversion if it exists -- bazelisk support
    bazelversion = os.path.join(repo_root, ".bazelversion")
    if os.path.exists(bazelversion):
        shutil.copy2(
            bazelversion, os.path.join(tmpdir, ".bazelversion")
        )


def run_bazel(tmpdir, action, target, extra_flags):
    """Run a bazel command in the workspace directory."""
    cmd = [
        "bazel",
        action,
        target,
        "--experimental_cc_implementation_deps",
        "--enable_bzlmod",
    ] + extra_flags
    print(f"Running: {' '.join(cmd)}")
    print(f"In directory: {tmpdir}")
    result = subprocess.run(
        cmd,
        cwd=tmpdir,
        capture_output=True,
        text=True,
    )
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print(f"stdout:\n{result.stdout}")
    if result.stderr:
        print(f"stderr:\n{result.stderr}")
    return result


def check_output_file(tmpdir, output_file, patterns):
    """Check that all patterns appear in the output file."""
    filepath = os.path.join(tmpdir, output_file)
    if not os.path.exists(filepath):
        print(f"FAIL: Output file does not exist: {filepath}")
        # List what's in bazel-bin to help debug
        bazel_bin = os.path.join(tmpdir, "bazel-bin")
        if os.path.exists(bazel_bin):
            print("Contents of bazel-bin:")
            for root, _, files in os.walk(bazel_bin):
                for f in files:
                    print(f"  {os.path.join(root, f)}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    for pattern in patterns:
        if not re.search(pattern, content):
            print(
                f"FAIL: Pattern not found in {output_file}: "
                f"{pattern}"
            )
            print(f"File content:\n{content}")
            sys.exit(1)
        print(f"PASS: Found pattern: {pattern}")


def cleanup(tmpdir):
    """Shut down bazel server to release file locks."""
    subprocess.run(
        ["bazel", "shutdown"],
        cwd=tmpdir,
        capture_output=True,
    )


def main():
    """Main entry point."""
    args = parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    print(f"Resolved repo root: {repo_root}")

    tmpdir = tempfile.mkdtemp(prefix="external_test_")
    print(f"Created temp workspace: {tmpdir}")

    try:
        setup_workspace(tmpdir, repo_root, args.srcs)

        result = run_bazel(
            tmpdir, args.action, args.target, args.extra_flags
        )

        if result.returncode != args.expected_exit_code:
            print(
                f"FAIL: Expected exit code {args.expected_exit_code}, "
                f"got {result.returncode}"
            )
            sys.exit(1)
        print(
            f"PASS: Exit code matches expected: "
            f"{args.expected_exit_code}"
        )

        if args.output_file and args.contains:
            check_output_file(
                tmpdir, args.output_file, args.contains
            )

        print("ALL CHECKS PASSED")
    finally:
        cleanup(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
