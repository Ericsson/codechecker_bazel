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

load("@rules_python//python:py_test.bzl", "py_test")

exports_files(["requirements.txt"])

# The whole repository is checked from the workspace file.
# Pylint comes from PyPI, see MODULE.bazel.
py_test(
    name = "pylint",
    size = "medium",
    srcs = ["pylint.py"],
    args = [
        "$(rootpath //:MODULE.bazel)",
        "--rcfile=$(location .pylintrc)",
        "--verbose",
        ".",
    ],
    data = [
        ".pylintrc",
        "//:MODULE.bazel",
    ],
    local = True,
    main = "pylint.py",
    tags = [
        "external",
        "pylint",
    ],
    deps = ["@pylint_deps//pylint"],
)
