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

load("@rules_cc//cc/common:cc_info.bzl", "CcInfo")
load("codechecker_config.bzl", "get_config_file")
load(
    "compile_commands.bzl",
    "SourceFilesInfo",
    "compile_commands_aspect",
    "compile_commands_impl",
)

# buildifier: disable=unused-variable
def _run_code_checker(
        ctx,
        per_file_script,
        src,
        arguments,
        info,
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
    codechecker_metadata_file_name = "{}/{}_metadata.json".format(*file_name_params)

    # Declare output files
    clang_tidy_plist = ctx.actions.declare_file(clang_tidy_plist_file_name)
    clangsa_plist = ctx.actions.declare_file(clangsa_plist_file_name)
    codechecker_log = ctx.actions.declare_file(codechecker_log_file_name)

    # Create skipfile
    config = ctx.actions.declare_file(
        "{}/{}_skipfile".format(*file_name_params),
    )
    ctx.actions.write(
        output = config,
        content = "\n".join(ctx.attr.skip),
    )

    codechecker_metadata = ctx.actions.declare_file(codechecker_metadata_file_name)

    if "--ctu" in options:
        inputs = [
            compile_commands_json,
            config_file,
            config,
        ] + sources_and_headers
    else:
        # NOTE: we collect only headers, so CTU may not work!
        headers = depset(transitive = target[SourceFilesInfo].headers.to_list())
        inputs = depset([
            compile_commands_json,
            config_file,
            src,
            config,
        ], transitive = [headers])

    outputs = [
        clang_tidy_plist,
        clangsa_plist,
        codechecker_log,
        codechecker_metadata,
    ]

    analyzer_output_paths = "clangsa," + clangsa_plist.path + \
                            ";clang-tidy," + clang_tidy_plist.path

    analyzer_executables = "clangsa:" + info.clangsa.path + \
                           ";clang-tidy:" + info.clang_tidy.path

    # Action to run CodeChecker for a file
    # env_vars are unused for now, since
    # use_default_shell_env and env are incompatible
    # TODO: use env for environment variables, instead of passing it as argument
    ctx.actions.run(
        inputs = inputs,
        outputs = outputs,
        executable = per_file_script,
        tools = [
            info.runfiles,
            ctx.attr._per_file_script[DefaultInfo].files_to_run,
        ],
        arguments = [
            info.codechecker.path,
            compile_commands_json.path,
            " ".join(options),
            config_file.path,
            data_dir,
            src.path,
            codechecker_log.path,
            config.path,
            codechecker_metadata.path,
            analyzer_output_paths,
            analyzer_executables,
        ],
        mnemonic = "CodeChecker",
        progress_message = "CodeChecker analyze {}".format(src.short_path),
    )
    return outputs

def check_valid_file_type(src):
    """
    Checks if the file is a cpp related file.

    Returns True if the file type matches one of the permitted
    srcs file types for C and C++ source files.
    Args:
        src: Path of a single source file.
    Returns:
        Boolean value.
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

def _per_file_impl(ctx):
    info = ctx.toolchains["//:toolchain_type"].codecheckerinfo
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
    config_file, env_vars = get_config_file(ctx)
    all_files = [compile_commands, config_file]

    # Create per_file_script
    per_file_script = ctx.actions.declare_file(ctx.label.name + "/per_file_script")
    ctx.actions.symlink(
        output = per_file_script,
        target_file = ctx.executable._per_file_script,
    )

    if ctx.attr.toolchain:
        info = ctx.attr.toolchain[platform_common.ToolchainInfo].codecheckerinfo
    else:
        info = ctx.toolchains["//:toolchain_type"].codecheckerinfo
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
                        per_file_script,
                        src,
                        args,
                        info,
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
            DATA_DIR=$(dirname {dirname})
            # ls -la $DATA_DIR/data
            # find $DATA_DIR/data -name *.plist -exec sed -i -e "s|<string>.*execroot/codechecker_bazel/|<string>|g" {{}} \\;
            # cat $DATA_DIR/data/test-src-lib.cc_clangsa.plist
            echo "Running: CodeChecker parse $DATA_DIR/data"
            $(realpath {codechecker}) parse $DATA_DIR/data
        """.format(dirname = ctx.outputs.test_script.short_path, codechecker = info.codechecker.short_path),
    )
    files = depset(
        direct = all_files,
    )
    run_files = [
        ctx.outputs.test_script,
    ] + info.runfiles.to_list() + all_files
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
        "config": attr.label(
            default = None,
            doc = "CodeChecker configuration",
        ),
        "default_options": attr.string_list(
            default = [
                "--analyzers clangsa clang-tidy",
                "--clean",
            ],
            doc = "List of default CodeChecker analyze options",
        ),
        "options": attr.string_list(
            default = [],
            doc = "List of CodeChecker options, e.g.: --ctu",
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
        "_per_file_script": attr.label(
            allow_files = True,
            executable = True,
            cfg = "target",
            default = ":per_file_script",
        ),
    },
    outputs = {
        "compile_commands": "%{name}/compile_commands.json",
        "test_script": "%{name}/test_script.sh",
    },
    test = True,
    toolchains = ["//:toolchain_type"],
)
