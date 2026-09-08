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
Per-target macro for running pylint on Python targets.

Lints the Python sources a target provides via `PyInfo.transitive_sources`.

Usage:
    load("//test/pylint:pylint_test.bzl", "pylint")

    pylint(
        name = "pylint",
        targets = [":my_py_binary"],
    )
"""

def _filter_py_sources(target):
    """Collect python files, written by us, provided by a target.

    Reads `PyInfo.transitive_sources` and drops files that live in an
    external repository (e.g. pip deps), keeping
    only files rooted in the main workspace.

    Args:
        target: A target that may carry PyInfo.

    Returns:
        A list of first-party python File objects (possibly empty).
    """
    if PyInfo not in target:
        return []

    sources = []
    for src in target[PyInfo].transitive_sources.to_list():
        if src.extension != "py":
            continue

        # Files from external repositories (e.g. pip)
        # have a non-empty owner or workspace root/name.
        owner = src.owner
        if owner.workspace_root or owner.workspace_name:
            continue
        sources.append(src)
    return sources

def _collect_sources(targets):
    """Union python sources across the given targets.

    Args:
        targets: List of targets to collect sources from.

    Returns:
        A depset of python File objects.
    """
    sources = []
    for target in targets:
        sources.extend(_filter_py_sources(target))

    return depset(sources)

def _pylint_impl(ctx):
    sources = _collect_sources(ctx.attr.targets)
    source_list = sources.to_list()

    # Write the manifest of files to lint.
    manifest = ctx.actions.declare_file(ctx.label.name + "_manifest.txt")
    ctx.actions.write(
        output = manifest,
        content = "\n".join([src.short_path for src in source_list]) + "\n",
    )

    executable = ctx.actions.declare_file(ctx.label.name)
    runner = ctx.executable._runner
    ctx.actions.write(
        output = executable,
        is_executable = True,
        content = """#!/usr/bin/env bash
set -euo pipefail
exec "{runner}" \
    --rcfile "{rcfile}" \
    --manifest "{manifest}" "$@"
""".format(
            runner = runner.short_path,
            rcfile = ctx.file.pylintrc.short_path,
            manifest = manifest.short_path,
        ),
    )

    runfiles = ctx.runfiles(
        files = source_list + [
            manifest,
            ctx.file.pylintrc,
        ],
    )
    runfiles = runfiles.merge(
        ctx.attr._runner[DefaultInfo].default_runfiles,
    )

    return [
        DefaultInfo(
            executable = executable,
            runfiles = runfiles,
        ),
    ]

_pylint_test = rule(
    implementation = _pylint_impl,
    test = True,
    attrs = {
        "pylintrc": attr.label(
            allow_single_file = True,
            mandatory = True,
            doc = "Label of the .pylintrc configuration file.",
        ),
        "targets": attr.label_list(
            mandatory = True,
            doc = "Python targets whose sources should be linted.",
        ),
        "_runner": attr.label(
            default = Label("//test/pylint:pylint_runner"),
            executable = True,
            cfg = "target",
        ),
    },
)

def pylint(
        name,
        targets,
        pylintrc = "//test/pylint:.pylintrc",
        tags = [],
        **kwargs):
    """Run pylint on the first-party sources of the given Python targets.

    Sources are collected transitively from ``PyInfo``, so a top-level
    target also lints the first-party libraries it imports.

    Args:
        name: Test name.
        targets: Python targets (py_binary/py_library/py_test) to lint.
        pylintrc: Label of the .pylintrc configuration file.
        tags: Additional test tags.
        **kwargs: Forwarded to the underlying rule.
    """
    pylint_tags = [] + tags
    if "pylint" not in pylint_tags:
        pylint_tags.append("pylint")

    _pylint_test(
        name = name,
        targets = targets,
        pylintrc = pylintrc,
        tags = pylint_tags,
        **kwargs
    )
