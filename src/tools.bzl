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

"""
Toolchain setup for python and CodeChecker
Provide tools used by more rulesets.
"""

def _codechecker_local_repository_impl(repository_ctx):
    codechecker_bin_path = repository_ctx.which("CodeChecker")
    if not codechecker_bin_path:
        fail("ERROR! CodeChecker is not detected")
    clang_bin_path = repository_ctx.which("clang")
    if not clang_bin_path:
        fail("ERROR! Clang is not detected")
    clang_tidy_bin_path = repository_ctx.which("clang-tidy")
    if not clang_tidy_bin_path:
        fail("ERROR! Clang-tidy is not detected")
    dirname_path = repository_ctx.which("dirname")
    if not dirname_path:
        fail("ERROR! dirname is not detected")
    defs = "CODECHECKER_BIN_PATH = '{}'\n".format(codechecker_bin_path)
    defs += "CLANG_BIN_PATH = '{}'\n".format(clang_bin_path)
    defs += "CLANG_TIDY_BIN_PATH = '{}'\n".format(clang_tidy_bin_path)
    defs += "BAZEL_VERSION = '{}'\n".format(native.bazel_version)
    repository_ctx.file(
        repository_ctx.path("defs.bzl"),
        content = defs,
        executable = False,
    )

    repository_ctx.symlink(codechecker_bin_path, "codechecker_bin")
    repository_ctx.symlink(clang_bin_path, "clang_bin")
    repository_ctx.symlink(clang_tidy_bin_path, "clang_tidy_bin")
    repository_ctx.symlink(dirname_path, "dirname_bin")

    repository_ctx.file(
        repository_ctx.path("BUILD"),
        content = """
filegroup(
    name = "CodeChecker",
    srcs = ["codechecker_bin"],
    visibility = ["//visibility:public"],
)
filegroup(
    name = "clang",
    srcs = ["clang_bin"],
    visibility = ["//visibility:public"],
)
filegroup(
    name = "clang_tidy",
    srcs = ["clang_tidy_bin"],
    visibility = ["//visibility:public"],
)
filegroup(
    name = "dirname",
    srcs = ["dirname_bin"],
    visibility = ["//visibility:public"],
)
        """,
        executable = False,
    )

default_codechecker_tools = repository_rule(
    attrs = {},
    local = True,
    doc = "Generate repository for default CodeChecker tools",
    implementation = _codechecker_local_repository_impl,
)

# buildifier: disable=unused-variable
# This parameter is provided, regardless if we use it or not
def register_default_codechecker_tools(ctx = None):
    default_codechecker_tools(name = "default_codechecker_tools")

# Define the extension here
module_register_default_codechecker_tools = module_extension(
    implementation = register_default_codechecker_tools,
)
