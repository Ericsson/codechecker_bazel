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

workspace(name = "codechecker_bazel")

load(
    "@codechecker_bazel//src:tools.bzl",
    "register_default_codechecker",
    "register_default_python_toolchain",
)

register_default_python_toolchain()
register_toolchains("@default_python_tools//:python_toolchain")

register_default_codechecker()
