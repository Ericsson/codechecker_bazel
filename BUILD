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

load("//src:codechecker_toolchain.bzl", "codechecker_toolchain")

# The public labels of rules_codechecker live here,
# the implementation is in //src
#
# NOTE: only load from packages visible to our consumers here,
# this package is loaded by everyone who resolves //:default_toolchain

# Named by convention
# https://bazel.build/extending/toolchains#writing-rules-toolchains
toolchain_type(
    name = "toolchain_type",
    visibility = ["//visibility:public"],
)

# Tools found on PATH, provisioned by the default_codechecker_tools extension
codechecker_toolchain(
    name = "default_tools",
    clang_tidy = "@default_codechecker_tools//:clang_tidy",
    clangsa = "@default_codechecker_tools//:clang",
    codechecker = "@default_codechecker_tools//:CodeChecker",
)

toolchain(
    name = "default_toolchain",
    toolchain = ":default_tools",
    toolchain_type = ":toolchain_type",
)

# Repository root marker, used by the buildifier and pylint tests
# to find the workspace root
exports_files(
    ["MODULE.bazel"],
    visibility = [
        "//test/buildifier:__pkg__",
        "//test/pylint:__pkg__",
    ],
)
