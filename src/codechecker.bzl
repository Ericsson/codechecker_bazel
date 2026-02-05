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
    "@default_codechecker_tools//:defs.bzl",
    "CODECHECKER_BIN_PATH",
)
load(
    "codechecker_config.bzl",
    "codechecker_config_internal",
    "get_config_file",
)
load(
    "common.bzl",
    "python_interpreter_tool",
    "python_path",
    "python_toolchain_type",
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

    codechecker_files = ctx.actions.declare_directory(ctx.label.name + "/codechecker-files")
    ctx.actions.expand_template(
        template = ctx.file._codechecker_script_template,
        output = ctx.outputs.codechecker_script,
        is_executable = False,
        substitutions = {
            "{Mode}": "Run",
            "{Verbosity}": "DEBUG",
            "{codechecker_bin}": CODECHECKER_BIN_PATH,
            "{compile_commands}": ctx.outputs.codechecker_commands.path,
            "{codechecker_skipfile}": ctx.outputs.codechecker_skipfile.path,
            "{codechecker_config}": config_file.path,
            "{codechecker_analyze}": " ".join(ctx.attr.analyze),
            "{codechecker_files}": codechecker_files.path,
            "{codechecker_log}": ctx.outputs.codechecker_log.path,
            "{codechecker_env}": codechecker_env,
        },
    )

    ctx.actions.run(
        inputs = depset(
            [
                ctx.outputs.codechecker_script,
                ctx.outputs.codechecker_commands,
                ctx.outputs.codechecker_skipfile,
                config_file,
            ] + source_files,
        ),
        outputs = [
            codechecker_files,
            ctx.outputs.codechecker_log,
        ],
        executable = python_path(ctx),
        tools = python_interpreter_tool(ctx),
        arguments = [ctx.outputs.codechecker_script.path],
        mnemonic = "CodeChecker",
        progress_message = "CodeChecker %s" % str(ctx.label),
        use_default_shell_env = True,
    )

    # List all files required at build and run (test) time
    all_files = [
        ctx.outputs.compile_commands,
        ctx.outputs.codechecker_commands,
        ctx.outputs.codechecker_skipfile,
        config_file,
        codechecker_files,
        ctx.outputs.codechecker_script,
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
        "targets": attr.label_list(
            aspects = [
                compile_commands_aspect,
            ],
            doc = "List of compilable targets which should be checked.",
        ),
        "skip": attr.string_list(
            default = [],
            doc = "List of skip/ignore file rules. " +
                  "See https://codechecker.readthedocs.io/en/latest/analyzer/user_guide/#skip-file",
        ),
        "config": attr.label(
            default = None,
            doc = "CodeChecker configuration",
        ),
        "analyze": attr.string_list(
            default = [],
            doc = "List of analyze command arguments, e.g.; --ctu.",
        ),
        "_compile_commands_filter": attr.label(
            allow_files = True,
            executable = True,
            cfg = "host",
            default = ":compile_commands_filter",
        ),
        "_codechecker_script_template": attr.label(
            default = ":codechecker_script.py",
            allow_single_file = True,
        ),
    },
    outputs = {
        "compile_commands": "%{name}/compile_commands.json",
        "codechecker_commands": "%{name}/codechecker_commands.json",
        "codechecker_skipfile": "%{name}/codechecker_skipfile.cfg",
        "codechecker_script": "%{name}/codechecker_script.py",
        "codechecker_log": "%{name}/codechecker.log",
    },
    toolchains = [python_toolchain_type()],
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

    # Create test script from template
    ctx.actions.expand_template(
        template = ctx.file._codechecker_script_template,
        output = ctx.outputs.codechecker_test_script,
        is_executable = True,
        substitutions = {
            "{Mode}": "Test",
            "{Verbosity}": "INFO",
            "{codechecker_bin}": CODECHECKER_BIN_PATH,
            "{codechecker_files}": codechecker_files.short_path,
            "{Severities}": " ".join(ctx.attr.severities),
        },
    )

    # For use in script the short path must be used (or absolute path)
    # For use in executable the full path
    python_interpreter_path = python_path(ctx)
    if python_interpreter_tool(ctx) != []:
        python_interpreter_path = python_interpreter_tool(ctx)[0].short_path

    ctx.actions.write(
        output = ctx.outputs.test_script_wrapper,
        is_executable = True,
        content = """
            {} {}
        """.format(
            python_interpreter_path,
            ctx.outputs.codechecker_test_script.short_path,
        ),
    )

    # Return test script and all required files
    run_files = default_runfiles + [
        ctx.outputs.codechecker_test_script,
        ctx.outputs.test_script_wrapper,
    ] + python_interpreter_tool(ctx)

    return [
        DefaultInfo(
            files = depset(all_files),
            runfiles = ctx.runfiles(files = run_files),
            executable = ctx.outputs.test_script_wrapper,
        ),
    ]

_codechecker_test = rule(
    implementation = _codechecker_test_impl,
    attrs = {
        "platform": attr.string(
            default = "",  #"@platforms//os:linux",
            doc = "Platform to build for",
        ),
        "targets": attr.label_list(
            aspects = [
                compile_commands_aspect,
            ],
            cfg = platforms_transition,
            doc = "List of compilable targets which should be checked.",
        ),
        "_compile_commands_filter": attr.label(
            allow_files = True,
            executable = True,
            cfg = "host",
            default = ":compile_commands_filter",
        ),
        "_codechecker_script_template": attr.label(
            default = ":codechecker_script.py",
            allow_single_file = True,
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
        "config": attr.label(
            default = None,
            cfg = platforms_transition,
            doc = "CodeChecker configuration",
        ),
        "analyze": attr.string_list(
            default = [],
            doc = "List of analyze command arguments, e.g. --ctu",
        ),
    } | version_specific_attributes(),
    outputs = {
        "compile_commands": "%{name}/compile_commands.json",
        "codechecker_commands": "%{name}/codechecker_commands.json",
        "codechecker_skipfile": "%{name}/codechecker_skipfile.cfg",
        "codechecker_script": "%{name}/codechecker_script.py",
        "codechecker_log": "%{name}/codechecker.log",
        "codechecker_test_script": "%{name}/codechecker_test_script.py",
        "test_script_wrapper": "%{name}/test_script_wrapper.sh",
    },
    toolchains = [python_toolchain_type()],
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
        **kwargs):
    """ Bazel test to run CodeChecker """
    codechecker_tags = [] + tags
    if "codechecker" not in tags:
        codechecker_tags.append("codechecker")
    if per_file:
        per_file_test(
            name = name,
            targets = targets,
            options = analyze,
            config = config,
            tags = tags,
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
    """ Bazel test suite to run CodeChecker for different platforms """
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
