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

# cc_binary for simple C++ tests
load(
    "@rules_cc//cc:defs.bzl",
    "cc_library",
)
load(
    "@rules_python//python:py_library.bzl",
    "py_library",
)
load(
    "@rules_python//python:py_test.bzl",
    "py_test",
)
load(
    "//:defs.bzl",
    "codechecker_test",
)

cc_library(
    name = "c_target",
    srcs = ["simple.c"],
    tags = ["manual"],
)

codechecker_test(
    name = "codechecker_data",
    tags = ["manual"],
    targets = [
        "c_target",
    ],
)

# codechecker_data is a test target, so its own $(rootpaths) resolve to the
# test launcher. This plain filegroup re-exports the analysis output files,
# letting the tests receive their paths from Bazel and pick the report
# directory (codechecker-files) instead of hard-coding it.
filegroup(
    name = "report_files",
    testonly = True,
    srcs = [":codechecker_data"],
    tags = ["manual"],
)

py_test(
    name = "parse_test",
    srcs = ["parse_check.py"],
    args = [
        "--mode=parse",
        "$(rootpaths :report_files)",
    ],
    data = [":report_files"],
    local = True,
    main = "parse_check.py",
    tags = ["unit"],
    deps = [":helpers"],
)

py_test(
    name = "parse_html_test",
    srcs = ["parse_check.py"],
    args = [
        "--mode=parse_html",
        "$(rootpaths :report_files)",
    ],
    data = [":report_files"],
    local = True,
    main = "parse_check.py",
    tags = ["unit"],
    deps = [":helpers"],
)

py_test(
    name = "store_test",
    size = "large",
    srcs = ["store_check.py"],
    args = ["$(rootpaths :report_files)"],
    data = [":report_files"],
    local = True,
    main = "store_check.py",
    tags = ["unit"],
    deps = [":helpers"],
)

py_library(
    name = "helpers",
    srcs = ["helpers.py"],
    imports = ["."],
)
