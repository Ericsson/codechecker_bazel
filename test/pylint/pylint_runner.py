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

"""Runner script for the pylint Bazel test.

Discovers .py files in given directories and runs pylint on them.
Uses a workspace marker file (like MODULE.bazel) to find the repo
root.

Pylint is imported as a Python dependency provided by Bazel,
not invoked from PATH.
"""

import argparse
import os
import pathlib
import sys

from pylint import lint


def workspace_root(marker):
    """Resolve the workspace root from a marker file."""
    return pathlib.Path(os.path.realpath(marker)).parent


def find_py_files(root, paths, exclude_patterns):
    """Find all .py files under the given paths."""
    files = []
    for p in paths:
        path = root / p
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            for py_file in sorted(path.rglob("*.py")):
                if not any(
                    py_file.match(pat)
                    for pat in exclude_patterns
                ):
                    files.append(py_file)
    return files


def main():
    """Parse arguments and run pylint on discovered sources."""
    parser = argparse.ArgumentParser(
        description="Run pylint on Python source files."
    )
    parser.add_argument(
        "--workspace",
        required=True,
        help="Path to a workspace marker file "
             "(e.g. MODULE.bazel) to locate the repo root.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Directories or .py files to lint "
             "(relative to workspace root).",
    )
    parser.add_argument(
        "--rcfile",
        default=None,
        help="Path to a .pylintrc configuration file.",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Glob patterns to exclude.",
    )
    args = parser.parse_args()

    root = workspace_root(args.workspace)
    sources = find_py_files(root, args.paths, args.exclude)

    if not sources:
        print("pylint_runner: no .py files found")
        sys.exit(1)

    # Change to the workspace root so that .pylintrc init-hook
    # (which uses os.getcwd()) can resolve project imports
    os.chdir(root)

    pylint_args = []
    if args.rcfile:
        rcfile_path = os.path.realpath(args.rcfile)
        pylint_args.append(f"--rcfile={rcfile_path}")
    pylint_args.extend(str(s) for s in sources)

    print(f"Running: pylint {' '.join(pylint_args)}")
    result = lint.Run(pylint_args, exit=False)
    sys.exit(result.linter.msg_status)


if __name__ == "__main__":
    main()
