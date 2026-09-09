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

"""Public API of rules_codechecker.

Usage:

    load("@rules_codechecker//:defs.bzl", "codechecker_test")
"""

# Clang rules, running without CodeChecker
load(
    "//src:clang.bzl",
    _clang_analyze_test = "clang_analyze_test",
    _clang_tidy_test = "clang_tidy_test",
)

# CodeChecker rules
load(
    "//src:codechecker.bzl",
    _codechecker_config = "codechecker_config",
    _codechecker_suite = "codechecker_suite",
    _codechecker_test = "codechecker_test",
    _get_platform_alias = "get_platform_alias",
)

# Toolchain rule, for providing custom tools
load(
    "//src:codechecker_toolchain.bzl",
    _codechecker_toolchain = "codechecker_toolchain",
)

# Compilation database (compile_commands.json) rule, aspect and provider
load(
    "//src:compile_commands.bzl",
    _SourceFilesInfo = "SourceFilesInfo",
    _compile_commands = "compile_commands",
    _compile_commands_aspect = "compile_commands_aspect",
    _platforms_transition = "platforms_transition",
)

# Store rule, for uploading results to a CodeChecker server
load(
    "//src:store.bzl",
    _store = "store",
)

codechecker_test = _codechecker_test
codechecker_suite = _codechecker_suite
codechecker_config = _codechecker_config
codechecker_toolchain = _codechecker_toolchain
compile_commands = _compile_commands
clang_tidy_test = _clang_tidy_test
clang_analyze_test = _clang_analyze_test
codechecker_store = _store

# Helper for the platform suffix codechecker_suite() adds to its test names
get_platform_alias = _get_platform_alias

# Building blocks for rules collecting the compilation database
compile_commands_aspect = _compile_commands_aspect
platforms_transition = _platforms_transition
SourceFilesInfo = _SourceFilesInfo
