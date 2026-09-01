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
load("@rules_python//python:py_binary.bzl", "py_binary")
load("@rules_python//python:py_library.bzl", "py_library")

py_library(
    name = "common",
    srcs = ["common.py"],
    imports = ["."],
    visibility = ["//visibility:public"],
)

# Tool filter compile_commands.json file
py_binary(
    name = "compile_commands_filter",
    srcs = ["compile_commands_filter.py"],
    visibility = ["//visibility:public"],
)

py_binary(
    name = "codechecker_script",
    srcs = ["codechecker_script.py"],
    visibility = ["//visibility:public"],
    deps = [":common"],
)

py_binary(
    name = "per_file_script",
    srcs = ["per_file_script.py"],
    visibility = ["//visibility:public"],
    deps = [":common"],
)

# The following are flags and default values for clang_tidy_aspect
filegroup(
    name = "clang_tidy_config_default",
    srcs = [],  # empty list: default configuration (.clang-tidy)
)

label_flag(
    name = "clang_tidy_config",
    build_setting_default = ":clang_tidy_config_default",
    visibility = ["//visibility:public"],
)

filegroup(
    name = "clang_tidy_executable_default",
    srcs = [],  # empty list: system clang-tidy
)

label_flag(
    name = "clang_tidy_executable",
    build_setting_default = ":clang_tidy_executable_default",
    visibility = ["//visibility:public"],
)

filegroup(
    name = "clang_tidy_additional_deps_default",
    srcs = [],
)

label_flag(
    name = "clang_tidy_additional_deps",
    build_setting_default = ":clang_tidy_additional_deps_default",
    visibility = ["//visibility:public"],
)
