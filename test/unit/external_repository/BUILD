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

load(
    "//test/unit/external_repository:external_test.bzl",
    "external_test",
)

exports_files([
    "external_test_runner.py",
    "main.cc",
    "intermediate.cpp",
    "intermediate.h",
])

external_test(
    name = "compile_commands_isystem_test",
    action = "build",
    contains = [
        "-isystem external/external_lib[~+]/include",
        "-isystem bazel-out/k8-fastbuild/bin/external/external_lib[~+]/include",
    ],
    output_file = "bazel-bin/compile_commands_isystem/compile_commands.json",
    target = ":compile_commands_isystem",
)

external_test(
    name = "codechecker_external_deps_test",
    target = ":codechecker_external_deps",
)

external_test(
    name = "per_file_external_deps_test",
    target = ":per_file_external_deps",
)

external_test(
    name = "codechecker_external_include_paths_test",
    extra_flags = ["--features=external_include_paths"],
    target = ":codechecker_external_deps",
)

external_test(
    name = "per_file_external_include_paths_test",
    extra_flags = ["--features=external_include_paths"],
    target = ":per_file_external_deps",
)
