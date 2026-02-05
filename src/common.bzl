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
Provide a collection of functions used by multiple bzl files.
"""

load("@default_codechecker_tools//:defs.bzl", "BAZEL_VERSION")

SOURCE_ATTR = [
    "srcs",
    "deps",
    "data",
    "exports",
    "implementation_deps",
]

def version_specific_attributes():
    """
    Returns a map of Bazel version specific attributes

    For instance:
    In older Bazel versions (e.g. 6) rulesets using transitions
    must have the attribute _whitelist_function_transition.
    In newer versions (e.g. 7) this is an error.
    """
    if BAZEL_VERSION.split(".")[0] in "0123456":
        return ({"_whitelist_function_transition": attr.label(
            default = "@bazel_tools//tools/whitelists/function_transition_whitelist",
            doc = "needed for transitions",
        )})
    return {}

def python_toolchain_type():
    """
    Returns version specific Python toolchain type
    """
    if BAZEL_VERSION.split(".")[0] in "01234567":
        return "@bazel_tools//tools/python:toolchain_type"
    return "@rules_python//python:toolchain_type"

def python_path(ctx):
    """
    Returns version specific Python path
    """
    py_toolchain = ctx.toolchains[python_toolchain_type()]
    if hasattr(py_toolchain, "py3_runtime_info"):
        py_runtime_info = py_toolchain.py3_runtime_info
        python_path = py_runtime_info.interpreter
    elif hasattr(py_toolchain, "py3_runtime"):
        py_runtime = py_toolchain.py3_runtime
        python_path = py_runtime.interpreter_path

        # @rules_python does not provide interpreter_path, but interpreter.path
        if python_path == None:
            python_path = py_runtime.interpreter.path
    else:
        fail("The resolved Python toolchain does not provide a Python3 runtime.")
    if not python_path:
        fail("The resolved Python toolchain does not provide a Python3 interpreter.")
    return python_path

def python_interpreter_tool(ctx):
    """
    Returns version specific Python interpreter object as only element in a list
    that is appropriate for the Bazel version that is running
    This list should be added to tools in ctx.action.run using it
    """
    py_toolchain = ctx.toolchains[python_toolchain_type()]
    python_interpreter = None
    if hasattr(py_toolchain, "py3_runtime"):
        py_runtime = py_toolchain.py3_runtime
        python_interpreter = py_runtime.interpreter
    if python_interpreter == None:
        return []
    return [python_interpreter]

def warning(ctx, msg):
    """
    Prints message if the debug tag is enabled.

    NOTE: "debug" in tags works only for rules, not aspects
    """
    if hasattr(ctx.attr, "tags") and "debug" in ctx.attr.tags:
        print(msg)
