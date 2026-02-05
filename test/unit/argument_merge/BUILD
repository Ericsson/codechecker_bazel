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

load(
    "//src:codechecker.bzl",
    "codechecker_test",
)

# cc_binary for simple C++ tests
load(
    "@rules_cc//cc:defs.bzl",
    "cc_library",
)

cc_library(
    name = "main",
    srcs = ["main.cc"],
)

# Test with overwriting analyzers argument
# Testing on the regular rule isn't necessary,
# there are no default options to be merged.
codechecker_test(
    name = "per_file_argument_merge",
    analyze = [
        "--analyzers clangsa clang-tidy",
    ],
    per_file = True,
    targets = [
        "main",
    ],
)
