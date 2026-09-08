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
Macro for running pylint on the repository's Python source files.

Usage:

    load("//test/pylint:pylint_test.bzl", "pylint_test")

    pylint_test(
        name = "pylint",
        exclude = [
            "**/__pycache__/**",
        ],
        paths = [
            "src",
        ],
        pylint = "@pylint_deps//pylint",
        pylintrc = ":.pylintrc",
        workspace = "//:MODULE.bazel",
    )
"""

load("@rules_python//python:py_test.bzl", "py_test")

def pylint_test(
        name,
        pylint,
        pylintrc,
        paths,
        workspace = "//:MODULE.bazel",
        exclude = ["**/__pycache__/**"],
        tags = [],
        **kwargs):
    """Run pylint on Python source files discovered from the given paths.

    Args:
        name: Test name.
        pylint: Label of the pylint pip package.
        pylintrc: Label of the .pylintrc configuration file.
        paths: Directories or .py files to lint (relative to workspace root).
        workspace: Label of a file at the workspace root, used to locate
                   the repository root at runtime.
        exclude: Glob patterns to exclude from linting.
        tags: Additional test tags.
        **kwargs: Forwarded to py_test.
    """
    pylint_tags = [] + tags
    if "pylint" not in tags:
        pylint_tags.append("pylint")

    # The runner discovers linted sources at runtime by walking the
    # tree from the workspace marker, so they are not in this action's
    # input set or cache key. Without "external", Bazel serves a stale
    # "(cached) PASSED" after a source changes; the tag forces a re-run.
    if "external" not in tags:
        pylint_tags.append("external")

    args = [
        "--workspace=$(rootpath {})".format(workspace),
        "--rcfile=$(rootpath {})".format(pylintrc),
    ]
    if exclude:
        args.append("--exclude")
        args.extend(exclude)
    args.append("--")
    args.extend(paths)

    py_test(
        name = name,
        srcs = ["//test/pylint:pylint_runner.py"],
        main = "//test/pylint:pylint_runner.py",
        args = args,
        data = [
            pylintrc,
            workspace,
        ],
        deps = [pylint],
        local = True,
        tags = pylint_tags,
        **kwargs
    )
