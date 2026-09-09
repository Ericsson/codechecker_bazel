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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""
CodeChecker store wrapper script.

Uploads CodeChecker analysis results to a remote server.
Symlinks report data to a writable temporary directory first,
because we need all analysis data in the same place.
Also Bazel output directories are read-only and
CodeChecker store needs to create temporary files inside
the report directory.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile


def parse_args(argv=None):
    """Parse command-line arguments.

    Returns a `(args, passthrough)` tuple where `args` holds the
    arguments consumed by this wrapper (`--codechecker_path` and
    `--files`) and `passthrough` is the list of arguments
    provided by the user as "real" command line argument.
    """
    parser = argparse.ArgumentParser(
        description="CodeChecker store wrapper"
    )
    parser.add_argument(
        "--codechecker_path",
        required=True,
        help="Path to the CodeChecker executable",
    )
    parser.add_argument(
        "--files",
        required=True,
        action="append",
        help=(
            "Path to a codechecker-files entry (may be repeated for "
            "multiple targets). Each entry is either a directory "
            "containing a 'data' subdirectory (monolithic "
            "codechecker_test) or an individual report file such as a "
            ".plist (per_file_test)."
        ),
    )
    args, passthrough = parser.parse_known_args(argv)
    return args, passthrough


def _symlink_tree(src_dir, dst_dir):
    """
    Recreate the directory tree of `src_dir` under `dst_dir`,
    creating real (writable) directories but symlinking each
    leaf file back to its original location.

    This gives CodeChecker store a writable top-level directory
    while avoiding a byte-for-byte copy of the (potentially large)
    report files, which live read-only in the Bazel output tree.
    """
    os.makedirs(dst_dir, exist_ok=True)
    for entry in os.listdir(src_dir):
        src = os.path.join(src_dir, entry)
        dst = os.path.join(dst_dir, entry)
        if os.path.isdir(src):
            _symlink_tree(src, dst)
        else:
            # Symlink to the absolute source so it resolves
            # regardless of the current working directory.
            if os.path.lexists(dst):
                os.remove(dst)
            os.symlink(os.path.realpath(src), dst)


def copy_data_to_tmpdir(codechecker_files_entries):
    """
    Build a single writable temporary directory that mirrors the
    report data from each codechecker-files entry.

    Directories are created as real, writable directories and the
    report files are symlinked in.

    Each entry is one of:
      * A directory (monolithic codechecker_test): its "data"
        subdirectory holds the report files, which are mirrored in.
      * An individual report file (per_file_test): plists, logs and
        metadata that already live directly under a "data" directory.
        These are symlinked in directly.

    Returns the path to the temporary directory containing
    the merged report files.
    """
    tmpdir = tempfile.mkdtemp(prefix="cc_store_")
    for entry in codechecker_files_entries:
        if os.path.isdir(entry):
            # Monolithic target: reports live in "<entry>/data".
            data_dir = os.path.join(entry, "data")
            if not os.path.isdir(data_dir):
                print(
                    f"WARNING: {data_dir} does not exist, "
                    "skipping.",
                    file=sys.stderr,
                )
                continue
            _symlink_tree(data_dir, tmpdir)
        elif os.path.isfile(entry):
            # per_file target: an individual report file. Only .plist
            # report files belong in the store directory.
            if not entry.endswith(".plist"):
                continue
            dst = os.path.join(tmpdir, os.path.basename(entry))
            if os.path.lexists(dst):
                os.remove(dst)
            os.symlink(os.path.realpath(entry), dst)
        else:
            print(
                f"WARNING: {entry} does not exist, skipping.",
                file=sys.stderr,
            )
    return tmpdir


def run_store(codechecker_path, tmpdir, store_args):
    """
    Execute CodeChecker store on the temporary directory.

    `store_args` is the list of extra arguments given by the user to
    `CodeChecker store` (e.g. --url, --name/-n, --trim-path-prefix).
    Returns the process exit code.
    """
    cmd = [
        codechecker_path,
        "store",
        tmpdir,
        *store_args,
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=False,
        check=False,
    )
    return result.returncode


def main():
    """Main entry point."""
    args, passthrough = parse_args()

    codechecker = os.path.realpath(args.codechecker_path)
    if not os.path.isfile(codechecker):
        print(
            f"ERROR: CodeChecker not found: {codechecker}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Copy report data to a writable location
    tmpdir = copy_data_to_tmpdir(args.files)

    try:
        ret = run_store(codechecker, tmpdir, passthrough)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    sys.exit(ret)


if __name__ == "__main__":
    main()
