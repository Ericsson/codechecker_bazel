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

load("@rules_cc//cc:defs.bzl", "cc_library")
load(
    ":analysis_test.bzl",
    "compile_flags_test_suite",
    "custom_ccinfo",
    "defines_from_impl_deps_test",
    "includes_from_impl_deps_test",
    "local_defines_in_impl_deps_test",
    "no_duplicates_test",
    "quote_includes_from_deps_test",
    "system_includes_from_impl_deps_test",
)

# =============================================================================
# Analysis tests
# =============================================================================

# get_compile_flags
# -----------------

cc_library(
    name = "compile_flags_tests_with_defines",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    defines = ["MY_DEFINE=1"],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_impl_dep_with_defines",
    srcs = ["testdata/bar.cc"],
    hdrs = ["testdata/bar.h"],
    defines = ["IMPL_DEP_DEFINE=1"],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_with_impl_dep_defines",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    implementation_deps = [":compile_flags_tests_impl_dep_with_defines"],
    tags = ["manual"],
)

defines_from_impl_deps_test(
    name = "defines_from_impl_deps",
    target_under_test = ":compile_flags_tests_with_impl_dep_defines",
)

cc_library(
    name = "compile_flags_tests_with_local_defines",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    local_defines = ["LOCAL_DEF=1"],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_impl_dep_with_local_defines",
    srcs = ["testdata/bar.cc"],
    hdrs = ["testdata/bar.h"],
    local_defines = ["IMPL_DEP_LOCAL_DEF=1"],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_with_impl_dep_local_defines",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    implementation_deps = [":compile_flags_tests_impl_dep_with_local_defines"],
    tags = ["manual"],
)

local_defines_in_impl_deps_test(
    name = "local_defines_in_impl_deps",
    target_under_test = ":compile_flags_tests_with_impl_dep_local_defines",
)

cc_library(
    name = "compile_flags_tests_with_includes",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    includes = ["my/include/path"],
    tags = ["manual"],
)

# includes from implementation_deps should be collected.
cc_library(
    name = "compile_flags_tests_impl_dep_with_includes",
    srcs = ["testdata/bar.cc"],
    hdrs = ["testdata/bar.h"],
    includes = ["impl_dep/include"],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_with_impl_dep_includes",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    implementation_deps = [":compile_flags_tests_impl_dep_with_includes"],
    tags = ["manual"],
)

includes_from_impl_deps_test(
    name = "includes_from_impl_deps",
    target_under_test = ":compile_flags_tests_with_impl_dep_includes",
)

cc_library(
    name = "compile_flags_tests_with_copts",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    copts = [
        "-Wall",
        "-Wextra",
    ],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_dep_with_includes",
    srcs = ["testdata/bar.cc"],
    hdrs = ["testdata/bar.h"],
    includes = ["dep/include"],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_with_dep_includes",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    tags = ["manual"],
    deps = [":compile_flags_tests_dep_with_includes"],
)

custom_ccinfo(
    name = "compile_flags_tests_sys_include_provider",
    system_includes = ["my/sys/include"],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_with_system_includes",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    tags = ["manual"],
    deps = [":compile_flags_tests_sys_include_provider"],
)

# system_includes from implementation_deps should be collected.
custom_ccinfo(
    name = "compile_flags_tests_impl_dep_sys_include_provider",
    system_includes = ["impl_dep/sys/include"],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_with_impl_dep_system_includes",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    implementation_deps = [":compile_flags_tests_impl_dep_sys_include_provider"],
    tags = ["manual"],
)

system_includes_from_impl_deps_test(
    name = "system_includes_from_impl_deps",
    target_under_test = ":compile_flags_tests_with_impl_dep_system_includes",
)

custom_ccinfo(
    name = "compile_flags_tests_quote_include_provider",
    quote_includes = ["my/quote/include"],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_with_quote_includes",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    tags = ["manual"],
    deps = [":compile_flags_tests_quote_include_provider"],
)

custom_ccinfo(
    name = "compile_flags_tests_dep_quote_include_provider",
    quote_includes = ["dep/quote/path"],
    tags = ["manual"],
)

cc_library(
    name = "compile_flags_tests_with_dep_quote_includes",
    srcs = ["testdata/foo.cc"],
    hdrs = ["testdata/foo.h"],
    implementation_deps = [":compile_flags_tests_dep_quote_include_provider"],
    tags = ["manual"],
)

quote_includes_from_deps_test(
    name = "quote_includes_from_deps",
    target_under_test = ":compile_flags_tests_with_dep_quote_includes",
)

compile_flags_test_suite(name = "compile_flags_tests")

no_duplicates_test(
    name = "no_duplicates",
    target_under_test = ":compile_flags_tests_with_dep_includes",
)
