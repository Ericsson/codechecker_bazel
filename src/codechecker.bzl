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
Rulesets for running codechecker in a single Bazel job.
"""

load(
    "codechecker_config.bzl",
    "codechecker_config_internal",
    "get_config_file",
)
load(
    "common.bzl",
    "version_specific_attributes",
)
load(
    "compile_commands.bzl",
    "compile_commands_aspect",
    "compile_commands_impl",
    "platforms_transition",
)
load(
    "per_file.bzl",
    "per_file_test",
)

def get_platform_alias(platform):
    """
    Get platform alias for full platform names being used

    Args:
        platform: A string containing the platform
    Returns:
    string: If the full platform name is consistent with
    valid syntax, returns the short alias to represent it.
    Returns the original platform passed otherwise
    """
    if platform.startswith("@platforms"):
        (_, _, shortname) = platform.partition(":")
        platform = shortname
    return platform

def _codechecker_impl(ctx):
    # Get compile_commands.json file and source files
    compile_commands = None
    source_files = None
    for output in compile_commands_impl(ctx):
        if type(output) == "DefaultInfo":
            compile_commands = output.files.to_list()[0]
            source_files = output.default_runfiles.files.to_list()
    if not compile_commands:
        fail("Failed to generate compile_commands.json file!")
    if not source_files:
        fail("Failed to collect source files!")
    if compile_commands != ctx.outputs.compile_commands:
        fail("Seems compile_commands.json file is incorrect!")

    # Convert flacc calls to clang in compile_commands.json
    # and save to codechecker_commands.json
    ctx.actions.run(
        inputs = [ctx.outputs.compile_commands],
        outputs = [ctx.outputs.codechecker_commands],
        executable = ctx.executable._compile_commands_filter,
        arguments = [
            # "-v",  # -vv for debug
            "--input=" + ctx.outputs.compile_commands.path,
            "--output=" + ctx.outputs.codechecker_commands.path,
        ],
        mnemonic = "CodeCheckerConvertFlaccToClang",
        progress_message = "Filtering %s" % str(ctx.label),
        # use_default_shell_env = True,
    )

    # Create CodeChecker skip (ignore) file
    ctx.actions.write(
        output = ctx.outputs.codechecker_skipfile,
        content = "\n".join(ctx.attr.skip),
        is_executable = False,
    )

    config_file, codechecker_env = get_config_file(ctx)

    if ctx.attr.toolchain:
        info = ctx.attr.toolchain[platform_common.ToolchainInfo].codecheckerinfo
    else:
        info = ctx.toolchains["//:toolchain_type"].codecheckerinfo

    codechecker_files = ctx.actions.declare_directory(ctx.label.name + "/codechecker-files")

    codechecker_script = ctx.attr._codechecker_script[DefaultInfo].files_to_run
    cmd_args = ctx.actions.args()
    cmd_args.add("--mode", "Run")
    cmd_args.add("--verbosity", "DEBUG")
    cmd_args.add("--codechecker_path", info.codechecker.path)
    cmd_args.add("--clang_tidy", info.clang_tidy.path)
    cmd_args.add("--clang", info.clangsa.path)
    cmd_args.add("--commands", ctx.outputs.codechecker_commands.path)
    cmd_args.add("--skip", ctx.outputs.codechecker_skipfile.path)
    cmd_args.add("--config", config_file.path)
    if len(ctx.attr.analyze) != 0:
        cmd_args.add("--analyze=" + " ".join(ctx.attr.analyze))
    cmd_args.add("--files", codechecker_files.path)
    cmd_args.add("--log", ctx.outputs.codechecker_log.path)
    cmd_args.add("--env", codechecker_env)
    ctx.actions.run(
        inputs = depset(
            [
                ctx.outputs.codechecker_commands,
                ctx.outputs.codechecker_skipfile,
                config_file,
            ] + source_files,
        ),
        tools = [
            info.runfiles,
            ctx.attr._codechecker_script[DefaultInfo].files_to_run,
        ],
        outputs = [
            codechecker_files,
            ctx.outputs.codechecker_log,
        ],
        executable = codechecker_script,
        arguments = [cmd_args],
        mnemonic = "CodeChecker",
        progress_message = "CodeChecker %s" % str(ctx.label),
        # use_default_shell_env = True,
    )

    # List all files required at build and run (test) time
    all_files = [
        ctx.outputs.compile_commands,
        ctx.outputs.codechecker_commands,
        ctx.outputs.codechecker_skipfile,
        config_file,
        codechecker_files,
        ctx.outputs.codechecker_log,
    ] + source_files

    # List files required for test
    run_files = [
        codechecker_files,
    ] + source_files

    # Return all files
    return [
        DefaultInfo(
            files = depset(all_files),
            runfiles = ctx.runfiles(files = run_files),
        ),
        OutputGroupInfo(
            codechecker_files = depset([codechecker_files]),
        ),
    ]

codechecker = rule(
    implementation = _codechecker_impl,
    attrs = {
        "analyze": attr.string_list(
            default = [],
            doc = "List of analyze command arguments, e.g.; --ctu.",
        ),
        "config": attr.label(
            default = None,
            doc = "CodeChecker configuration",
        ),
        "skip": attr.string_list(
            default = [],
            doc = "List of skip/ignore file rules. " +
                  "See https://codechecker.readthedocs.io/en/latest/analyzer/user_guide/#skip-file",
        ),
        "targets": attr.label_list(
            aspects = [
                compile_commands_aspect,
            ],
            doc = "List of compilable targets which should be checked.",
        ),
        "toolchain": attr.label(
            default = None,
            doc = "Optional toolchain() target. " +
                  "When set, tools from this target are used instead of " +
                  "Bazel's toolchain resolution.",
        ),
        "_codechecker_script": attr.label(
            allow_files = True,
            executable = True,
            cfg = "target",
            default = ":codechecker_script",
        ),
        "_compile_commands_filter": attr.label(
            allow_files = True,
            executable = True,
            cfg = "exec",
            default = ":compile_commands_filter",
        ),
    },
    outputs = {
        "codechecker_commands": "%{name}/codechecker_commands.json",
        "codechecker_log": "%{name}/codechecker.log",
        "codechecker_skipfile": "%{name}/codechecker_skipfile.cfg",
        "compile_commands": "%{name}/compile_commands.json",
    },
    toolchains = [
        "//:toolchain_type",
    ],
)

def _codechecker_test_impl(ctx):
    # Run CodeChecker at build step
    info = _codechecker_impl(ctx)
    all_files = []
    default_runfiles = []
    codechecker_files = []
    for output in info:
        if type(output) == "DefaultInfo":
            all_files = output.files.to_list()
            default_runfiles = output.default_runfiles.files.to_list()
        if type(output) == "OutputGroupInfo":
            codechecker_files = output.codechecker_files.to_list()[0]
    if not all_files:
        fail("Files required for codechecker test are not available")
    if not codechecker_files:
        fail("Execution results required for codechecker test are not available")

    if ctx.attr.toolchain:
        info = ctx.attr.toolchain[platform_common.ToolchainInfo].codecheckerinfo
    else:
        info = ctx.toolchains["//:toolchain_type"].codecheckerinfo

    # Create test script
    codechecker_test_script = ctx.actions.declare_file(ctx.label.name + "/codechecker_test_script")
    ctx.actions.symlink(
        output = codechecker_test_script,
        target_file = ctx.executable._codechecker_script,
    )

    launcher = ctx.actions.declare_file(ctx.label.name + "_launcher.sh")
    ctx.actions.write(
        output = launcher,
        content = """#!/bin/bash
            exec {tool} --mode=Test --verbosity=INFO \
            --codechecker_path '{codechecker_path}' \
            --files '{codechecker_files}' --severities '{severities}'
            """.format(
            tool = ctx.outputs.codechecker_test_script.short_path,
            codechecker_path = info.codechecker.path,
            codechecker_files = codechecker_files.short_path,
            severities = " ".join(ctx.attr.severities),
        ),
        is_executable = True,
    )

    # Return test script and all required files
    run_files = default_runfiles + [
        ctx.outputs.codechecker_test_script,
        launcher,
    ] + info.runfiles.to_list()
    all_runfiles = ctx.runfiles(files = run_files)

    # Add runfiles from the py_binary target:
    all_runfiles = all_runfiles.merge(ctx.attr._codechecker_script[DefaultInfo].default_runfiles)
    return [
        DefaultInfo(
            files = depset(all_files),
            runfiles = all_runfiles,
            executable = launcher,
        ),
    ]

_codechecker_test = rule(
    implementation = _codechecker_test_impl,
    attrs = {
        "analyze": attr.string_list(
            default = [],
            doc = "List of analyze command arguments, e.g. --ctu",
        ),
        "config": attr.label(
            default = None,
            cfg = platforms_transition,
            doc = "CodeChecker configuration",
        ),
        "platform": attr.string(
            default = "",  #"@platforms//os:linux",
            doc = "Platform to build for",
        ),
        "severities": attr.string_list(
            default = ["HIGH"],
            doc = "List of defect severities: HIGH, MEDIUM, LOW, STYLE etc",
        ),
        "skip": attr.string_list(
            default = [],
            doc = "List of skip/ignore file rules. " +
                  "See https://codechecker.readthedocs.io/en/latest/analyzer/user_guide/#skip-file",
        ),
        "targets": attr.label_list(
            aspects = [
                compile_commands_aspect,
            ],
            cfg = platforms_transition,
            doc = "List of compilable targets which should be checked.",
        ),
        "toolchain": attr.label(
            default = None,
            doc = "Optional toolchain() target. " +
                  "When set, tools from this target are used instead of " +
                  "Bazel's toolchain resolution.",
        ),
        "_codechecker_script": attr.label(
            allow_files = True,
            executable = True,
            cfg = "target",
            default = ":codechecker_script",
        ),
        "_compile_commands_filter": attr.label(
            allow_files = True,
            executable = True,
            cfg = "exec",
            default = ":compile_commands_filter",
        ),
    } | version_specific_attributes(),
    outputs = {
        "codechecker_commands": "%{name}/codechecker_commands.json",
        "codechecker_log": "%{name}/codechecker.log",
        "codechecker_skipfile": "%{name}/codechecker_skipfile.cfg",
        "codechecker_test_script": "%{name}/codechecker_test_script",
        "compile_commands": "%{name}/compile_commands.json",
    },
    toolchains = [
        "//:toolchain_type",
    ],
    test = True,
)

def codechecker_test(
        name,
        targets,
        platform = "",  #"@platforms//os:linux",
        severities = ["HIGH"],
        skip = [],
        config = None,
        analyze = [],
        tags = [],
        per_file = False,
        toolchain = None,
        **kwargs):
    """
    Macro to choose the appropriate codechecker rule

    Args:
        name: Name of the target invoking CodeChecker.
        targets: List of targets to be analyzed by CodeChecker.
        platform: Platform to be analyzed on.
        severities: List of warning levels that should be considered failing.
        skip: Skip patterns for CodeChecker.
        config: Config target for CodeChecker.
        analyze: List of analyze command arguments.
        tags: Bazel tags
        per_file: Boolean value, toggles wether to run the analysis
                  with the experimental per_file rule.
        toolchain: Optional toolchain() target.
                  When set, tools from this target are used instead of
                  Bazel's toolchain resolution.
        **kwargs: Other miscellaneous arguments.
    Returns:
        none
    """
    codechecker_tags = [] + tags
    if "codechecker" not in tags:
        codechecker_tags.append("codechecker")
    if per_file:
        per_file_test(
            name = name,
            targets = targets,
            options = analyze,
            skip = skip,
            config = config,
            toolchain = toolchain,
            tags = codechecker_tags,
            **kwargs
        )
    else:
        _codechecker_test(
            name = name,
            platform = platform,
            targets = targets,
            severities = severities,
            skip = skip,
            config = config,
            analyze = analyze,
            toolchain = toolchain,
            tags = codechecker_tags,
            **kwargs
        )

def codechecker_suite(
        name,
        targets,
        platforms = [""],  #["@platforms//os:linux"],
        severities = ["HIGH"],
        skip = [],
        config = None,
        analyze = [],
        tags = [],
        **kwargs):
    """
    Bazel test suite to run CodeChecker for different platforms

    Args:
        name: Name of the target invoking CodeChecker.
        targets: List of targets to be analyzed by CodeChecker.
        platforms: List of platform to be analyzed on.
        severities: List of warning levels that should be considered failing.
        skip: Skip patterns for CodeChecker.
        config: Config target for CodeChecker.
        analyze: List of analyze command arguments.
        tags: Bazel tags
        **kwargs: Other miscellaneous arguments.
    Returns:
        none
    """
    tests = []
    for platform in platforms:
        shortname = get_platform_alias(platform)
        if not shortname:
            shortname = "default"
        test_name = name + "." + shortname
        tests.append(test_name)
        codechecker_test(
            name = test_name,
            platform = platform,
            targets = targets,
            severities = severities,
            skip = skip,
            config = config,
            analyze = analyze,
            tags = tags,
        )
    native.test_suite(
        name = name,
        tests = tests,
        tags = tags,
        **kwargs
    )

# This rule definition is here for compatibility reasons
# in the earliest versions, the entire codechecker_config definition was here,
# but was later moved to its own .bzl file.
# This macro is left here so that early adopters
# don't need to change where the rule is loaded from.
def codechecker_config(
        name,
        analyze = [],
        parse = [],
        config_file = None,
        env = [],
        **kwargs):
    codechecker_config_internal(
        name = name,
        analyze = analyze,
        parse = parse,
        config_file = config_file,
        env = env,
        **kwargs
    )
