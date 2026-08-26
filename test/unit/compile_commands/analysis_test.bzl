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
Analysis-phase tests for compile_commands.bzl.

Tests the following functions indirectly via compile_commands_aspect:
  - collect_headers
  - get_sources
  - get_compile_flags
  - _cc_compiler_info
"""

load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts")
load(
    "//src:compile_commands.bzl",
    "SourceFilesInfo",
    "compile_commands_aspect",
)

# =============================================================================
# Helper rules
# =============================================================================

def _custom_ccinfo_impl(ctx):
    """Rule that provides a CcInfo with custom include paths and defines."""
    compilation_context = cc_common.create_compilation_context(
        defines = depset(ctx.attr.defines),
        system_includes = depset(ctx.attr.system_includes),
        quote_includes = depset(ctx.attr.quote_includes),
        includes = depset(ctx.attr.includes),
    )
    return [CcInfo(compilation_context = compilation_context)]

custom_ccinfo = rule(
    implementation = _custom_ccinfo_impl,
    attrs = {
        "defines": attr.string_list(default = []),
        "includes": attr.string_list(default = []),
        "quote_includes": attr.string_list(default = []),
        "system_includes": attr.string_list(default = []),
    },
)

# =============================================================================
# Helpers
# =============================================================================

def _get_compile_commands(source_files_info):
    """Extract command strings from SourceFilesInfo.compilation_db."""
    return [entry.command for entry in source_files_info.compilation_db.to_list()]

# =============================================================================
# Compilation flag collection tests
# =============================================================================

def _defines_test_impl(ctx):
    """defines appear as -D in the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    asserts.true(env, len(commands) > 0, "Should have at least one compile command")
    asserts.true(
        env,
        "MY_DEFINE" in commands[0],
        "Should contain define MY_DEFINE, got: %s" % commands[0],
    )

    return analysistest.end(env)

defines_test = analysistest.make(
    _defines_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _defines_from_impl_deps_test_impl(ctx):
    """defines from implementation_deps appear as -D in the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    foo_commands = [c for c in commands if "foo.cc" in c]
    asserts.true(env, len(foo_commands) > 0, "Should have a command for foo.cc")

    asserts.true(
        env,
        "IMPL_DEP_DEFINE" in foo_commands[0],
        "Should contain define IMPL_DEP_DEFINE from implementation_dep, got: %s" % foo_commands[0],
    )

    return analysistest.end(env)

defines_from_impl_deps_test = analysistest.make(
    _defines_from_impl_deps_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _local_defines_test_impl(ctx):
    """local_defines appear as -D in the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    asserts.true(env, len(commands) > 0, "Should have at least one compile command")
    asserts.true(
        env,
        "LOCAL_DEF" in commands[0],
        "Should contain local_define LOCAL_DEF, got: %s" % commands[0],
    )

    return analysistest.end(env)

local_defines_test = analysistest.make(
    _local_defines_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _local_defines_in_impl_deps_test_impl(ctx):
    """local_defines from implementation_deps are local to the dep's own sources."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    foo_commands = [c for c in commands if "foo.cc" in c]
    asserts.true(env, len(foo_commands) > 0, "Should have a command for foo.cc")

    asserts.false(
        env,
        "IMPL_DEP_LOCAL_DEF" in foo_commands[0],
        "Should not contain local_define IMPL_DEP_LOCAL_DEF from " +
        "implementation_dep, got: %s" % foo_commands[0],
    )

    bar_commands = [c for c in commands if "bar.cc" in c]
    asserts.true(env, len(bar_commands) > 0, "Should have a command for bar.cc")

    asserts.true(
        env,
        "IMPL_DEP_LOCAL_DEF" in bar_commands[0],
        "Should contain local_define IMPL_DEP_LOCAL_DEF from " +
        "implementation_dep, got: %s" % bar_commands[0],
    )

    return analysistest.end(env)

local_defines_in_impl_deps_test = analysistest.make(
    _local_defines_in_impl_deps_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _includes_test_impl(ctx):
    """includes appear as -I in the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    asserts.true(env, len(commands) > 0, "Should have at least one compile command")
    asserts.true(
        env,
        "my/include/path" in commands[0],
        "Should contain include path, got: %s" % commands[0],
    )

    return analysistest.end(env)

includes_test = analysistest.make(
    _includes_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _includes_from_impl_deps_test_impl(ctx):
    """includes from implementation_deps propagate to the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    foo_commands = [c for c in commands if "foo.cc" in c]
    asserts.true(env, len(foo_commands) > 0, "Should have a command for foo.cc")
    asserts.true(
        env,
        "impl_dep/include" in foo_commands[0],
        "Should contain impl_dep's include path, got: %s" % foo_commands[0],
    )

    return analysistest.end(env)

includes_from_impl_deps_test = analysistest.make(
    _includes_from_impl_deps_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _copts_test_impl(ctx):
    """The copts flags are passed through to the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    asserts.true(env, len(commands) > 0, "Should have at least one compile command")
    asserts.true(
        env,
        "-Wall" in commands[0],
        "Should contain -Wall, got: %s" % commands[0],
    )
    asserts.true(
        env,
        "-Wextra" in commands[0],
        "Should contain -Wextra, got: %s" % commands[0],
    )

    return analysistest.end(env)

copts_test = analysistest.make(
    _copts_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _dep_includes_test_impl(ctx):
    """includes from deps propagate to the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    foo_commands = [c for c in commands if "foo.cc" in c]
    asserts.true(env, len(foo_commands) > 0, "Should have a command for foo.cc")
    asserts.true(
        env,
        "dep/include" in foo_commands[0],
        "Should contain dep's include path, got: %s" % foo_commands[0],
    )

    return analysistest.end(env)

dep_includes_test = analysistest.make(
    _dep_includes_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _system_includes_test_impl(ctx):
    """system_includes appear as -isystem in the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    asserts.true(env, len(commands) > 0, "Should have at least one compile command")
    asserts.true(
        env,
        "-isystem my/sys/include" in commands[0],
        "Should contain -isystem my/sys/include, got: %s" % commands[0],
    )

    return analysistest.end(env)

system_includes_test = analysistest.make(
    _system_includes_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _system_includes_from_impl_deps_test_impl(ctx):
    """system_includes from implementation_deps appear as -isystem in the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    foo_commands = [c for c in commands if "foo.cc" in c]
    asserts.true(env, len(foo_commands) > 0, "Should have a command for foo.cc")
    asserts.true(
        env,
        "-isystem impl_dep/sys/include" in foo_commands[0],
        "Should contain -isystem impl_dep/sys/include from implementation_dep, got: %s" % foo_commands[0],
    )

    return analysistest.end(env)

system_includes_from_impl_deps_test = analysistest.make(
    _system_includes_from_impl_deps_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _quote_includes_test_impl(ctx):
    """quote_includes appear as -iquote in the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    asserts.true(env, len(commands) > 0, "Should have at least one compile command")
    asserts.true(
        env,
        "-iquote my/quote/include" in commands[0],
        "Should contain -iquote my/quote/include, got: %s" % commands[0],
    )

    return analysistest.end(env)

quote_includes_test = analysistest.make(
    _quote_includes_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _quote_includes_from_deps_test_impl(ctx):
    """quote_includes from implementation_deps appear as -iquote in the compile command."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    foo_commands = [c for c in commands if "foo.cc" in c]
    asserts.true(env, len(foo_commands) > 0, "Should have a command for foo.cc")

    asserts.true(
        env,
        "-iquote dep/quote/path" in foo_commands[0],
        "Should contain -iquote dep/quote/path from implementation_dep, got: %s" % foo_commands[0],
    )

    return analysistest.end(env)

quote_includes_from_deps_test = analysistest.make(
    _quote_includes_from_deps_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

def _no_duplicates_test_impl(ctx):
    """Compile flags should not contain duplicates."""
    env = analysistest.begin(ctx)
    commands = _get_compile_commands(analysistest.target_under_test(env)[SourceFilesInfo])

    foo_commands = [c for c in commands if "foo.cc" in c]
    asserts.true(env, len(foo_commands) > 0, "Should have a command for foo.cc")

    # Split command into flag+value pairs and check for duplicates.
    # If a token starts with "-" it begins a new flag; otherwise it's the
    # value of the previous flag (e.g. "-I /path" becomes one entry).
    tokens = foo_commands[0].split(" ")
    flags = []
    for t in tokens:
        if t == "":
            continue
        if t.startswith("-") or len(flags) == 0:
            flags.append(t)
        else:
            flags[-1] = flags[-1] + " " + t

    seen = []
    duplicates = []
    for f in flags:
        if f in seen and f not in duplicates:
            duplicates.append(f)
        seen.append(f)

    asserts.true(
        env,
        len(duplicates) == 0,
        "Compile command should not have duplicate flags, found: %s" % duplicates,
    )

    return analysistest.end(env)

no_duplicates_test = analysistest.make(
    _no_duplicates_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

# =============================================================================
# Test suites
# =============================================================================

def compile_flags_test_suite(name):
    """Analysis tests for compile command generation.

    Args:
        name: the name prefix for the test suite.
    """
    defines_test(
        name = name + "_defines_test",
        target_under_test = ":" + name + "_with_defines",
    )
    local_defines_test(
        name = name + "_local_defines_test",
        target_under_test = ":" + name + "_with_local_defines",
    )
    includes_test(
        name = name + "_includes_test",
        target_under_test = ":" + name + "_with_includes",
    )
    copts_test(
        name = name + "_copts_test",
        target_under_test = ":" + name + "_with_copts",
    )
    dep_includes_test(
        name = name + "_dep_includes_test",
        target_under_test = ":" + name + "_with_dep_includes",
    )
    system_includes_test(
        name = name + "_system_includes_test",
        target_under_test = ":" + name + "_with_system_includes",
    )
    quote_includes_test(
        name = name + "_quote_includes_test",
        target_under_test = ":" + name + "_with_quote_includes",
    )

    native.test_suite(
        name = name,
        tests = [
            ":" + name + "_defines_test",
            ":" + name + "_local_defines_test",
            ":" + name + "_includes_test",
            ":" + name + "_copts_test",
            ":" + name + "_dep_includes_test",
            ":" + name + "_system_includes_test",
            ":" + name + "_quote_includes_test",
        ],
    )
