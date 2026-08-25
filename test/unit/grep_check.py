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
Validates wether a list of patterns is found in a file

This test reads a file and asserts that all provided patterns
are present within its contents.

Intended to be used as the main of a py_test Bazel target.
"""

import argparse
import glob
import re
import sys


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    Returns:
        Parsed arguments containing the file path and list of patterns.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Assert that all given patterns exist in the provided file."
        )
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Path or glob pattern to the file(s) to search within.",
    )
    parser.add_argument(
        "--missing_files",
        default=[],
        nargs="+",
        required=False,
        help="Path or glob pattern to the file(s) that shouldn't exists.",
    )
    parser.add_argument(
        "--contains",
        nargs="+",
        action="extend",
        required=False,
        help="One or more string to assert are present in the file(s).",
    )
    parser.add_argument(
        "--excludes",
        nargs="+",
        action="extend",
        required=False,
        help="One or more string to assert are not present in the file(s).",
    )
    parser.add_argument(
        "--once",
        nargs="+",
        action="extend",
        required=False,
        help="One or more string to assert are present exactly once "
        "in the file(s), for instance to detect duplicated flags.",
    )
    parser.add_argument(
        "--regex_patterns",
        nargs="+",
        action="extend",
        required=False,
        help="One or more patterns to assert are present in the file(s).",
    )
    parser.add_argument(
        "--any",
        required=False,
        action="store_true",
        help="If provided, the program will succeed if at least one file "
        "contains the patterns",
    )
    return parser.parse_args()


def check_args(args):
    """Checks wether the arguments are correct, aborts if not"""
    if (not args.contains and not args.excludes and
            not args.regex_patterns and not args.once):
        fail("  [ERROR] Must define at least one pattern or negative pattern.")


def exact_match(pattern: str, content: str) -> bool:
    """Default search: checks if pattern is exactly in content."""
    return pattern in content


def single_match(pattern: str, content: str) -> bool:
    """Checks if pattern is in content exactly once."""
    return content.count(pattern) == 1


def check_patterns(
    content: str,
    patterns: list[str],
    search=exact_match,
    negative: bool = False,
) -> tuple[bool, set[str], set[str]]:
    """
    Checks wether a string contains every pattern in a list.

    Args:
        content: Text to search in.
        patterns: List of search patterns.
        search: Function with signature func(pattern, content) -> bool.
                Defaults to `pattern in content`.
        negative: Boolean, wether to check patterns as positive or negative.
    Returns:
        bool - Wether all patterns are correctly (not) found.
        set[str] - Set of patterns that are correctly (not) found.
        set[str] - Set of patterns that are incorrectly (not) found.
    """
    all_passed = True
    found_patterns = set()
    missing_pattern = set()
    for pattern in patterns:
        if bool(search(pattern, content)) == negative:
            missing_pattern.add(pattern)
            all_passed = False
        else:
            found_patterns.add(pattern)
    return all_passed, found_patterns, missing_pattern


def check_file(content: str, args) -> tuple[bool, set[str], set[str]]:
    """
    Checks if file contains all regexes.
    Returns boolean value, and set of patterns correctly identified.
    """
    all_passed = True
    found_patterns = set()
    missing_patterns = set()

    groups = [
        (args.contains, exact_match, False),
        (args.excludes, exact_match, True),
        (args.once, single_match, False),
        (args.regex_patterns, re.search, False),
    ]

    for patterns, search, negative in groups:
        if patterns:
            group_pass, found, missing = check_patterns(
                content, patterns, search, negative
            )
            all_passed = all_passed and group_pass
            found_patterns.update(found)
            missing_patterns.update(missing)

    return all_passed, found_patterns, missing_patterns


def assert_expectedly_missing_files(files):
    """
    Asserts that none of the files exist in `files`.
    """
    for file_pattern in files:
        matched_files = glob.glob(file_pattern, recursive=True)
        if matched_files:
            print(f"\n{file_pattern} unexpectedly exists.")
            sys.exit(1)


def fail(msg: str, exit_code: int = 1):
    """
    Exits the program, with a message
    """
    print(msg)
    sys.exit(exit_code)


def collect_file_paths(glob_list: list[str]) -> list[str]:
    """Convert the glob patterns into a list of file paths"""
    file_paths = []
    for file_pattern in glob_list:
        matched_files = glob.glob(file_pattern, recursive=True)
        if not matched_files:
            # Each file pattern must match at least a file
            fail(f"  [WARN] No files matched pattern/path: '{file_pattern}'")
        file_paths.extend(matched_files)

    if not file_paths:
        fail("  [ERR] No file collected to be checked.")
    return file_paths


def main() -> None:
    """Entry point for the pattern-matching test."""
    args = parse_args()
    check_args(args)

    assert_expectedly_missing_files(args.missing_files)

    files_to_check = [x for x in args.files if x not in args.missing_files]
    if not files_to_check:
        print(
            "There is no files to check, "
            "since all files are expected to not exits"
        )
        sys.exit(0)

    file_paths = collect_file_paths(files_to_check)

    all_passed = True
    found_patterns = set()
    missing_patterns = set()

    for file in file_paths:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            all_found_in_file, patterns_in_file, missing_patterns_in_file = (
                check_file(content, args)
            )
            all_passed = all_passed and all_found_in_file
            found_patterns.update(patterns_in_file)
            for pattern in missing_patterns_in_file:
                missing_patterns.add((file, pattern))

    if args.any:
        patterns = (
            (args.contains or [])
            + (args.excludes or [])
            + (args.once or [])
            + (args.regex_patterns or [])
        )

        all_passed = all(pattern in found_patterns for pattern in patterns)

    if not all_passed:
        for file, pattern in missing_patterns:
            print(f"Missing pattern {pattern} in file {file}")
        fail("\nOne or more patterns missing. Test FAILED.")


if __name__ == "__main__":
    main()
