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
    "cc_binary",
    "cc_library",
)

# Prototype for CodeChecker analyze --file
# NOTE: CodeChecker analyze --file --ctu does not work
load(
    "@bazel_codechecker//src:code_checker.bzl",
    "code_checker_test",
)

# Test defect in CTU mode
cc_library(
    name = "linking",
    hdrs = ["linking.h"],
)

# Test defect in CTU mode
cc_library(
    name = "secondary",
    srcs = ["secondary.cc"],
    deps = ["linking"],
)

# Simplest C++ test which should PASS
cc_binary(
    name = "primary",
    srcs = ["primary.cc"],
    deps = [
        "secondary",
        "linking"
    ],
)

code_checker_test(
    name = "code_checker_caching",
    targets = [
        "primary",
    ],
)
