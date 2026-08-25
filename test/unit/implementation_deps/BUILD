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
    "@rules_cc//cc:defs.bzl",
    "cc_library",
)
load(
    "//:defs.bzl",
    "codechecker_test",
    "compile_commands",
)
load(
    "//test/unit:unit_test.bzl",
    "unit_test",
)

cc_library(
    name = "dep_lib",
    srcs = [
        "dep.cpp",
    ],
    hdrs = ["dep.h"],
    tags = ["manual"],
)

cc_library(
    name = "main_lib",
    srcs = [
        "main.cpp",
    ],
    implementation_deps = ["dep_lib"],
    tags = ["manual"],
)

compile_commands(
    name = "compile_commands_implementation_deps",
    tags = ["manual"],
    targets = [
        ":main_lib",
    ],
)

codechecker_test(
    name = "codechecker_implementation_deps",
    tags = ["manual"],
    targets = [
        ":main_lib",
    ],
)

codechecker_test(
    name = "per_file_implementation_deps",
    per_file = True,
    tags = ["manual"],
    targets = [
        ":main_lib",
    ],
)

unit_test(
    name = "codechecker_implementation_deps_test",
    contains = [
        "core.DivideZero",
        "cplusplus.NewDeleteLeaks",
    ],
    data = [":codechecker_implementation_deps"],
    files = "test/unit/implementation_deps/codechecker_implementation_deps/codechecker.log",
)

unit_test(
    name = "per_file_implementation_deps_test",
    contains = [
        "core.DivideZero",
        "cplusplus.NewDeleteLeaks",
    ],
    data = [":per_file_implementation_deps"],
    files = "test/unit/implementation_deps/per_file_implementation_deps/**/*.plist",
    require_patterns_in_each_file = False,
)

unit_test(
    name = "compile_commands_implementation_deps_test",
    contains = [
        "main.cpp",
        "dep.cpp",
    ],
    data = [":compile_commands_implementation_deps"],
    files = "test/unit/implementation_deps/compile_commands_implementation_deps/compile_commands.json",
)

# Header only dependency declaring one flag of every kind.
# It has no sources, therefore the compile commands of its consumers contain
# their own source only, and every flag found there comes from this dependency.
# Bazel propagates defines and includes through deps, but never through
# implementation_deps, and never propagates local_defines at all.
cc_library(
    name = "flagged_dep_lib",
    hdrs = glob(["inc/*.h"]),
    defines = ["PROPAGATED_DEFINE=1"],
    includes = ["inc"],
    local_defines = ["PRIVATE_DEFINE=1"],
    tags = ["manual"],
)

cc_library(
    name = "flagged_implementation_deps_lib",
    srcs = ["main.cpp"],
    implementation_deps = [":flagged_dep_lib"],
    tags = ["manual"],
)

# Control for the test above: with deps Bazel propagates the flags itself
cc_library(
    name = "flagged_deps_lib",
    srcs = ["main.cpp"],
    tags = ["manual"],
    deps = [":flagged_dep_lib"],
)

# The same dependency in both attributes, its flags are collected twice
cc_library(
    name = "duplicated_dep_lib",
    srcs = ["main.cpp"],
    implementation_deps = [":flagged_dep_lib"],
    tags = ["manual"],
    deps = [":flagged_dep_lib"],
)

# local_defines of the target itself belong to its own compile line
cc_library(
    name = "own_local_defines_lib",
    srcs = ["main.cpp"],
    local_defines = ["OWN_PRIVATE_DEFINE=1"],
    tags = ["manual"],
)

compile_commands(
    name = "compile_commands_flagged_implementation_deps",
    tags = ["manual"],
    targets = [
        ":flagged_implementation_deps_lib",
    ],
)

compile_commands(
    name = "compile_commands_flagged_deps",
    tags = ["manual"],
    targets = [
        ":flagged_deps_lib",
    ],
)

compile_commands(
    name = "compile_commands_duplicated_dep",
    tags = ["manual"],
    targets = [
        ":duplicated_dep_lib",
    ],
)

compile_commands(
    name = "compile_commands_own_local_defines",
    tags = ["manual"],
    targets = [
        ":own_local_defines_lib",
    ],
)

# implementation_deps does not propagate, the aspect must collect the flags of
# the dependency explicitly, except its local_defines which stay private
unit_test(
    name = "compile_commands_flagged_implementation_deps_test",
    contains = [
        "-isystem test/unit/implementation_deps/inc",
        "-D'PROPAGATED_DEFINE=1'",
    ],
    data = [":compile_commands_flagged_implementation_deps"],
    excludes = ["-D'PRIVATE_DEFINE=1'"],
    files = "test/unit/implementation_deps/compile_commands_flagged_implementation_deps/compile_commands.json",
)

# deps propagates the same flags without any collection in the aspect
unit_test(
    name = "compile_commands_flagged_deps_test",
    contains = [
        "-isystem test/unit/implementation_deps/inc",
        "-D'PROPAGATED_DEFINE=1'",
    ],
    data = [":compile_commands_flagged_deps"],
    excludes = ["-D'PRIVATE_DEFINE=1'"],
    files = "test/unit/implementation_deps/compile_commands_flagged_deps/compile_commands.json",
)

# Flags of a dependency reachable through both attributes are not duplicated
unit_test(
    name = "compile_commands_duplicated_dep_test",
    data = [":compile_commands_duplicated_dep"],
    files = "test/unit/implementation_deps/compile_commands_duplicated_dep/compile_commands.json",
    once = [
        "-isystem test/unit/implementation_deps/inc",
        "-D'PROPAGATED_DEFINE=1'",
    ],
)

unit_test(
    name = "compile_commands_own_local_defines_test",
    contains = ["-D'OWN_PRIVATE_DEFINE=1'"],
    data = [":compile_commands_own_local_defines"],
    files = "test/unit/implementation_deps/compile_commands_own_local_defines/compile_commands.json",
)

# TODO: cover the local_includes attribute of cc_library.
# local_includes is counterpart of local_defines:
# it is added to compile flags of the target itself
# and is not propagated to the targets depending on it.
# See https://bazel.build/reference/be/c-cpp
