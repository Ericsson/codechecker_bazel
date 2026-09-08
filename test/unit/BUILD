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

load("@rules_python//python:py_library.bzl", "py_library")
load("//test/pylint:pylint_test.bzl", "pylint")

exports_files(["grep_check.py"])

# Library wrapping the unit_test runner so it can be linted.
py_library(
    name = "grep_check_lib",
    srcs = ["grep_check.py"],
    tags = ["manual"],
)

pylint(
    name = "pylint",
    targets = [":grep_check_lib"],
)
