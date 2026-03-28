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

"""
Macro for generating FOSS integration tests for rules_codechecker.

Each foss_test() generates a local py_test that:
  1. Downloads a FOSS project into a temp directory
  2. Sets up a standalone Bazel project with rules_codechecker
  3. Runs "bazel build" on codechecker targets to verify the rules work
  4. Validates the outputs (compile_commands.json, codechecker artifacts)

Example:
    foss_test(
        name = "zlib",
        url = "https://github.com/madler/zlib/archive/<commit>.tar.gz",
        tests = [":codechecker_test", ":compile_commands"],
    )
"""

load("@rules_python//python:defs.bzl", "py_test")

def foss_test(
        name,
        url,
        tests,
        target = None,
        tags = [],
        size = "large",
        **kwargs):
    """Generate a py_test that runs rules_codechecker on a FOSS project.

    Args:
        name: Test name.
        url: URL to the source archive (.tar.gz).
        tests: Analysis targets to build (e.g. codechecker_test, compile_commands).
        target: The cc_library target to analyze. Defaults to ":<name>".
        tags: Additional test tags.
        size: Test size (default: enormous, as these download + run bazel).
        **kwargs: Forwarded to py_test.
    """
    if target == None:
        target = ":" + name

    py_test(
        name = name,
        srcs = ["foss_test_runner.py"],
        main = "foss_test_runner.py",
        args = [
            "-vvv",
            "--url=" + url,
            "--target=" + target,
            "--tests",
        ] + tests,
        local = True,
        tags = ["foss", "external"] + tags,
        size = size,
        **kwargs
    )
