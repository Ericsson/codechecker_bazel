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
Macro for generating unit tests for rules_codechecker.

Each unit_test() generates a local py_test that:
    Depends on an other action, and checks for patterns on its output.

Example:
    unit_test(
        name = "my_unit_test",
        files = ["my_target_file.ext"],
        contains = ["my_pattern"],
        excludes = ["my_negative_pattern"],
        regex_patterns = ["my_.*regex.*_pattern"],
    )
"""

load("@rules_python//python:py_test.bzl", "py_test")

def unit_test(
        name,
        files,
        expected_missing_files = [],
        contains = None,
        excludes = None,
        once = None,
        regex_patterns = None,
        require_patterns_in_each_file = True,
        tags = [],
        size = "medium",
        **kwargs):
    """Generate a py_test that checks if provided patterns are in the files.

    Args:
        name: Test name.
        files: Path or glob to the files to be checked.
        expected_missing_files: Path or glob that should not exists.
                                If these are in the `files` list too,
                                disregard the missing file error.
        contains: Text that should be inside the files.
        excludes: Text that shouldn't be inside the files.
        once: Text that should be inside the files exactly once.
        regex_patterns: Regex patterns that should be found inside the files.
        require_patterns_in_each_file: If False its enough if every pattern is found in at least one file.
        tags: Additional test tags.
        size: Test size (default: medium).
        **kwargs: Forwarded to py_test.
    """
    if type(files) == "string":
        files = [files]
    if type(expected_missing_files) == "string":
        expected_missing_files = [expected_missing_files]
    if type(contains) == "string":
        contains = [contains]
    if type(excludes) == "string":
        excludes = [excludes]
    if type(once) == "string":
        once = [once]
    if type(regex_patterns) == "string":
        regex_patterns = [regex_patterns]

    python_args = ["--files"] + files
    if expected_missing_files:
        python_args.append("--missing_files")
        python_args.extend(expected_missing_files)
    if contains:
        # Pass every pattern with = so that patterns starting with a dash,
        # like compiler flags, are not parsed as options
        python_args.extend(
            ["--contains=\"{}\"".format(pat) for pat in contains],
        )
    if excludes:
        # Pass every pattern with = so that patterns starting with a dash,
        # like compiler flags, are not parsed as options
        python_args.extend(
            ["--excludes=\"{}\"".format(pat) for pat in excludes],
        )
    if once:
        # Pass every pattern with = so that patterns starting with a dash,
        # like compiler flags, are not parsed as options
        python_args.extend(
            ["--once=\"{}\"".format(pat) for pat in once],
        )
    if regex_patterns:
        # Pass every pattern with = so that patterns starting with a dash,
        # like compiler flags, are not parsed as options
        python_args.extend(
            ["--regex_patterns=\"{}\"".format(pat) for pat in regex_patterns],
        )
    if not require_patterns_in_each_file:
        python_args.append("--any")

    py_test(
        name = name,
        srcs = ["//test/unit:grep_check.py"],
        main = "//test/unit:grep_check.py",
        args = python_args,
        local = True,
        tags = ["unit"] + tags,
        size = size,
        **kwargs
    )
