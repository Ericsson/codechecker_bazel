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

load("@rules_python//python:py_binary.bzl", "py_binary")
load("//test/pylint:pylint_test.bzl", "pylint")

exports_files([
    ".pylintrc",
    "pylint_runner.py",
    "requirements.txt",
])

py_binary(
    name = "pylint_runner",
    srcs = ["pylint_runner.py"],
    main = "pylint_runner.py",
    visibility = ["//visibility:public"],
    deps = ["@pylint_deps//pylint"],
)

# Lint the pylint runner itself.
pylint(
    name = "pylint",
    targets = [":pylint_runner"],
)
