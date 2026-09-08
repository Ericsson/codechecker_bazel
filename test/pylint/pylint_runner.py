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

"""Runner script for the per-target pylint Bazel test.

Reads a manifest of .py files (produced by the pylint rule) and runs
pylint on exactly those files. Imports are resolved from this runner's
own sys.path, which rules_python populates from the linted target's
runfiles; no repository-root chdir is needed.

Pylint is imported as a Python dependency provided by Bazel,
not invoked from PATH.
"""

import argparse
import os
import sys

from pylint import lint


def read_manifest(manifest):
    """Read the list of files to lint from the manifest."""
    files = []
    with open(manifest, encoding="utf-8") as handle:
        for line in handle:
            entry = line.strip()
            if entry:
                files.append(entry)
    return files


def main():
    """Parse arguments and run pylint on the manifest sources."""
    parser = argparse.ArgumentParser(
        description="Run pylint on Python source files."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to a manifest file listing the .py files to lint.",
    )
    parser.add_argument(
        "--rcfile",
        default=None,
        help="Path to a .pylintrc configuration file.",
    )
    args = parser.parse_args()

    rcfile_path = os.path.realpath(args.rcfile) if args.rcfile else None
    sources = [os.path.realpath(s) for s in read_manifest(args.manifest)]

    if not sources:
        print("pylint_runner: no .py files found")
        sys.exit(1)

    pylint_args = []
    if rcfile_path:
        pylint_args.append(f"--rcfile={rcfile_path}")
    pylint_args.extend(sources)

    print(f"Running: pylint {' '.join(pylint_args)}")
    result = lint.Run(pylint_args, exit=False)
    sys.exit(result.linter.msg_status)


if __name__ == "__main__":
    main()
