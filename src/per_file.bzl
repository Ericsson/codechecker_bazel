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
Rulesets for running codechecker in a different Bazel action
for each translation unit.
"""

load("@bazel_tools//tools/build_defs/cc:action_names.bzl", "ACTION_NAMES")
load("@bazel_tools//tools/cpp:toolchain_utils.bzl", "find_cpp_toolchain")
load("@default_codechecker_tools//:defs.bzl", "BAZEL_VERSION")
load("codechecker_config.bzl", "get_config_file")
load(
    "common.bzl",
    "python_interpreter_tool",
    "python_path",
    "python_toolchain_type",
)
load(
    "compile_commands.bzl",
    "SourceFilesInfo",
    "compile_commands_aspect",
    "compile_commands_impl",
    "platforms_transition",
)

def _run_code_checker(
        ctx,
        src,
        arguments,
        target,
        label,
        options,
        config_file,
        env_vars,
        compile_commands_json,
        compilation_context,
        sources_and_headers):
    # Define Plist and log file names
    data_dir = ctx.attr.name + "/data"
    file_name_params = (data_dir, src.path.replace("/", "-"))
    clang_tidy_plist_file_name = "{}/{}_clang-tidy.plist".format(*file_name_params)
    clangsa_plist_file_name = "{}/{}_clangsa.plist".format(*file_name_params)
    codechecker_log_file_name = "{}/{}_codechecker.log".format(*file_name_params)

    # Declare output files
    clang_tidy_plist = ctx.actions.declare_file(clang_tidy_plist_file_name)
    clangsa_plist = ctx.actions.declare_file(clangsa_plist_file_name)
    codechecker_log = ctx.actions.declare_file(codechecker_log_file_name)

    if "--ctu" in options:
        inputs = [
            ctx.outputs.per_file_script,
            compile_commands_json,
            config_file,
        ] + sources_and_headers
    else:
        # NOTE: we collect only headers, so CTU may not work!
        headers = depset(transitive = target[SourceFilesInfo].headers.to_list())
        inputs = depset(
            [
                ctx.outputs.per_file_script,
                compile_commands_json,
                config_file,
                src,
            ],
            transitive = [headers],
        )

    outputs = [clang_tidy_plist, clangsa_plist, codechecker_log]

    analyzer_output_paths = "clangsa," + clangsa_plist.path + \
                            ";clang-tidy," + clang_tidy_plist.path

    # Action to run CodeChecker for a file
    ctx.actions.run(
        inputs = inputs,
        outputs = outputs,
        executable = python_path(ctx),
        tools = python_interpreter_tool(ctx),
        arguments = [
            ctx.outputs.per_file_script.path,
            data_dir,
            src.path,
            codechecker_log.path,
            analyzer_output_paths,
        ],
        mnemonic = "CodeChecker",
        use_default_shell_env = True,
        progress_message = "CodeChecker analyze {}".format(src.short_path),
    )
    return outputs

def check_valid_file_type(src):
    """
    Returns True if the file type matches one of the permitted
    srcs file types for C and C++ source files.
    """
    permitted_file_types = [
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".c++",
        ".C",
    ]
    for file_type in permitted_file_types:
        if src.basename.endswith(file_type):
            return True
    return False

def _collect_all_sources_and_headers(ctx):
    # NOTE: we are only using this function for CTU
    all_files = []
    for target in ctx.attr.targets:
        if not CcInfo in target:
            continue
        if SourceFilesInfo in target:
            if (hasattr(target[SourceFilesInfo], "transitive_source_files") and
                hasattr(target[SourceFilesInfo], "headers")):
                srcs = target[SourceFilesInfo].transitive_source_files.to_list()
                headers = depset(
                    transitive = target[SourceFilesInfo].headers.to_list(),
                ).to_list()
                all_files += srcs
                all_files += headers
    return all_files

def _create_wrapper_script(ctx, options, compile_commands_json, config_file):
    options_str = ""
    for item in options:
        options_str += item + " "
    ctx.actions.expand_template(
        template = ctx.file._per_file_script_template,
        output = ctx.outputs.per_file_script,
        is_executable = False,
        substitutions = {
            "{compile_commands_json}": compile_commands_json.path,
            "{codechecker_args}": options_str,
            "{config_file}": config_file.path,
        },
    )

def _per_file_impl(ctx):
    compile_commands = None
    for output in compile_commands_impl(ctx):
        if type(output) == "DefaultInfo":
            compile_commands = output.files.to_list()[0]
    if not compile_commands:
        fail("Failed to generate compile_commands.json file!")
    if compile_commands != ctx.outputs.compile_commands:
        fail("Seems compile_commands.json file is incorrect!")
    sources_and_headers = _collect_all_sources_and_headers(ctx)
    options = ctx.attr.default_options + ctx.attr.options
    all_files = [compile_commands]
    config_file, env_vars = get_config_file(ctx)
    _create_wrapper_script(ctx, options, compile_commands, config_file)
    for target in ctx.attr.targets:
        if not CcInfo in target:
            continue
        if SourceFilesInfo in target:
            if hasattr(target[SourceFilesInfo], "transitive_source_files"):
                srcs = target[SourceFilesInfo].transitive_source_files.to_list()
                all_files += srcs
                compilation_context = target[CcInfo].compilation_context
                for src in srcs:
                    if not check_valid_file_type(src):
                        continue
                    args = target[SourceFilesInfo].compilation_db.to_list()
                    outputs = _run_code_checker(
                        ctx,
                        src,
                        args,
                        target,
                        ctx.attr.name,
                        options,
                        config_file,
                        env_vars,
                        compile_commands,
                        compilation_context,
                        sources_and_headers,
                    )
                    all_files += outputs
    ctx.actions.write(
        output = ctx.outputs.test_script,
        is_executable = True,
        content = """
            DATA_DIR=$(dirname {})
            # ls -la $DATA_DIR/data
            # find $DATA_DIR/data -name *.plist -exec sed -i -e "s|<string>.*execroot/codechecker_bazel/|<string>|g" {{}} \\;
            # cat $DATA_DIR/data/test-src-lib.cc_clangsa.plist
            echo "Running: CodeChecker parse $DATA_DIR/data"
            CodeChecker parse $DATA_DIR/data
        """.format(ctx.outputs.test_script.short_path),
    )
    files = depset(
        direct = all_files,
    )
    run_files = [ctx.outputs.test_script] + all_files
    return [
        DefaultInfo(
            files = files,
            runfiles = ctx.runfiles(files = run_files),
            executable = ctx.outputs.test_script,
        ),
    ]

per_file_test = rule(
    implementation = _per_file_impl,
    attrs = {
        "options": attr.string_list(
            default = [],
            doc = "List of CodeChecker options, e.g.: --ctu",
        ),
        "default_options": attr.string_list(
            default = [
                "--analyzers clangsa clang-tidy",
                "--clean",
            ],
            doc = "List of default CodeChecker analyze options",
        ),
        "targets": attr.label_list(
            aspects = [
                compile_commands_aspect,
            ],
            doc = "List of compilable targets which should be checked.",
        ),
        "config": attr.label(
            default = None,
            doc = "CodeChecker configuration",
        ),
        "_per_file_script_template": attr.label(
            default = ":per_file_script.py",
            allow_single_file = True,
        ),
    },
    outputs = {
        "compile_commands": "%{name}/compile_commands.json",
        "test_script": "%{name}/test_script.sh",
        "per_file_script": "%{name}/per_file_script.py",
    },
    toolchains = [python_toolchain_type()],
    test = True,
)
