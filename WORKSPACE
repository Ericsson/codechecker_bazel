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
)
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "rules_python",
    sha256 = "ca2671529884e3ecb5b79d6a5608c7373a82078c3553b1fa53206e6b9dddab34",
    strip_prefix = "rules_python-0.38.0",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.38.0/rules_python-0.38.0.tar.gz",
)

load("@rules_python//python:repositories.bzl", "py_repositories")

py_repositories()

register_default_codechecker()
