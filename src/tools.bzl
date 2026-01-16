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
Toolchain setup for CodeChecker
Provide tools used by more rulesets.
"""


def _codechecker_local_repository_impl(repository_ctx):
    repository_ctx.file(
        repository_ctx.path("BUILD"),
        content = "",
        executable = False,
    )

    codechecker_bin_path = repository_ctx.which("CodeChecker")
    if not codechecker_bin_path:
        fail("ERROR! CodeChecker is not detected")

    defs = "CODECHECKER_BIN_PATH = '{}'\n".format(codechecker_bin_path)
    defs += "BAZEL_VERSION = '{}'\n".format(native.bazel_version)
    repository_ctx.file(
        repository_ctx.path("defs.bzl"),
        content = defs,
        executable = False,
    )

default_codechecker_tools = repository_rule(
    attrs = {},
    local = True,
    doc = "Generate repository for default CodeChecker tools",
    implementation = _codechecker_local_repository_impl,
)

def register_default_codechecker(ctx = None):
    default_codechecker_tools(name = "default_codechecker_tools")

# Define the extension here
module_register_default_codechecker = module_extension(
    implementation = register_default_codechecker,
)
