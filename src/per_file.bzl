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
load("codechecker_config.bzl", "get_config_file")
load("common.bzl", "SOURCE_ATTR")

def _run_code_checker(
        ctx,
        src,
        arguments,
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
        inputs = [ctx.outputs.per_file_script,
                  compile_commands_json, config_file] + sources_and_headers
    else:
        # NOTE: we collect only headers, so CTU may not work!
        headers = depset([src], transitive = [compilation_context.headers])
        inputs = depset(
            [
                ctx.outputs.per_file_script,
                compile_commands_json,
                config_file,
                src
            ], transitive = [headers])

    outputs = [clang_tidy_plist, clangsa_plist, codechecker_log]

    analyzer_output_paths = "clangsa," + clangsa_plist.path + \
                        ";clang-tidy," + clang_tidy_plist.path

    py_toolchain = ctx.toolchains["@rules_python//python:toolchain_type"].py3_runtime
    # Action to run CodeChecker for a file
    ctx.actions.run(
        inputs = inputs,
        outputs = outputs,
        executable = py_toolchain.interpreter,
        arguments = [
            ctx.outputs.per_file_script.path,
            data_dir,
            src.path,
            codechecker_log.path,
            analyzer_output_paths
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

def _rule_sources(ctx):
    srcs = []
    if hasattr(ctx.rule.attr, "srcs"):
        for src in ctx.rule.attr.srcs:
            srcs += [src for src in src.files.to_list() if check_valid_file_type(src)]
    return srcs

def _toolchain_flags(ctx, action_name = ACTION_NAMES.cpp_compile):
    cc_toolchain = find_cpp_toolchain(ctx)
    feature_configuration = cc_common.configure_features(
        ctx = ctx,
        cc_toolchain = cc_toolchain,
    )
    user_comp_flag_builder = ctx.fragments.cpp.copts
    if action_name == ACTION_NAMES.cpp_compile:
        user_comp_flag_builder += ctx.fragments.cpp.cxxopts
    elif action_name == ACTION_NAMES.c_compile:
        user_comp_flag_builder += ctx.fragments.cpp.conlyopts
    else:
        fail("Unhandled action name!")
    compile_variables = cc_common.create_compile_variables(
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        user_compile_flags = user_comp_flag_builder,
    )
    flags = cc_common.get_memory_inefficient_command_line(
        feature_configuration = feature_configuration,
        action_name = action_name,
        variables = compile_variables,
    )
    compiler = cc_common.get_tool_for_action(
        feature_configuration = feature_configuration,
        action_name = action_name,
    )
    return [compiler] + flags

def _compile_args(compilation_context):
    compile_args = []
    for define in compilation_context.defines.to_list():
        compile_args.append("-D" + define)
    for define in compilation_context.local_defines.to_list():
        compile_args.append("-D" + define)
    for include in compilation_context.framework_includes.to_list():
        compile_args.append("-F" + include)
    for include in compilation_context.includes.to_list():
        compile_args.append("-I" + include)
    for include in compilation_context.quote_includes.to_list():
        compile_args.append("-iquote " + include)
    for include in compilation_context.system_includes.to_list():
        compile_args.append("-isystem " + include)
    return compile_args

def _safe_flags(flags):
    # Some flags might be used by GCC, but not understood by Clang.
    # Remove them here, to allow users to run clang-tidy, without having
    # a clang toolchain configured (that would produce a good command line with --compiler clang)
    unsupported_flags = [
        "-fno-canonical-system-headers",
        "-fstack-usage",
    ]

    return [flag for flag in flags if flag not in unsupported_flags]

CompileInfo = provider(
    doc = "Source files and corresponding compilation arguments",
    fields = {
        "arguments": "dict: file -> list of arguments",
    },
)

def _compile_info_sources(deps):
    sources = []
    if type(deps) == "list":
        for dep in deps:
            if CompileInfo in dep:
                if hasattr(dep[CompileInfo], "arguments"):
                    srcs = dep[CompileInfo].arguments.keys()
                    sources += srcs
    return sources

def _collect_all_sources(ctx):
    sources = _rule_sources(ctx)
    for attr in SOURCE_ATTR:
        if hasattr(ctx.rule.attr, attr):
            deps = getattr(ctx.rule.attr, attr)
            sources += _compile_info_sources(deps)

    # Remove duplicates
    sources = depset(sources).to_list()
    return sources

def _compile_info_aspect_impl(target, ctx):
    if not CcInfo in target:
        return []
    compilation_context = target[CcInfo].compilation_context

    rule_flags = ctx.rule.attr.copts if hasattr(ctx.rule.attr, "copts") else []
    c_flags = _safe_flags(_toolchain_flags(ctx, ACTION_NAMES.c_compile) + rule_flags)  # + ["-xc"]
    cxx_flags = _safe_flags(_toolchain_flags(ctx, ACTION_NAMES.cpp_compile) + rule_flags)  # + ["-xc++"]

    srcs = _collect_all_sources(ctx)

    compile_args = _compile_args(compilation_context)
    arguments = {}
    for src in srcs:
        if src.extension.lower() in ["c"]:
            flags = c_flags
        elif src.extension.lower() in ["cc", "cpp", "cxx", "c++"]:
            flags = cxx_flags
        else:
            print("Unknown file extension for", src.short_path, "defaulting to C++ compile flags")
            flags = cxx_flags
        arguments[src] = flags + compile_args + [src.path]
    return [
        CompileInfo(
            arguments = arguments,
        ),
    ]

compile_info_aspect = aspect(
    implementation = _compile_info_aspect_impl,
    fragments = ["cpp"],
    attrs = {
        "_cc_toolchain": attr.label(default = Label("@bazel_tools//tools/cpp:current_cc_toolchain")),
    },
    attr_aspects = SOURCE_ATTR,
    toolchains = ["@bazel_tools//tools/cpp:toolchain_type"],
)

def _compile_commands_json(compile_commands):
    json_file = "[\n"
    entries = [json.encode(entry) for entry in compile_commands]
    json_file += ",\n".join(entries)
    json_file += "]\n"
    return json_file

def _compile_commands_data(ctx):
    compile_commands = []
    for target in ctx.attr.targets:
        if not CcInfo in target:
            continue
        if CompileInfo in target:
            if hasattr(target[CompileInfo], "arguments"):
                srcs = target[CompileInfo].arguments.keys()
                for src in srcs:
                    args = target[CompileInfo].arguments[src]

                    # print("args =", str(args))
                    record = struct(
                        file = src.path,
                        command = " ".join(args),
                        directory = ".",
                    )
                    compile_commands.append(record)
    return compile_commands

def _compile_commands_impl(ctx):
    compile_commands = _compile_commands_data(ctx)
    content = _compile_commands_json(compile_commands)
    file_name = ctx.attr.name + "/data/compile_commands.json"
    compile_commands_json = ctx.actions.declare_file(file_name)
    ctx.actions.write(
        output = compile_commands_json,
        content = content,
    )
    return compile_commands_json

def _collect_all_sources_and_headers(ctx):
    # NOTE: we are only using this function for CTU
    all_files = []
    headers = depset()
    for target in ctx.attr.targets:
        if not CcInfo in target:
            continue
        if CompileInfo in target:
            if hasattr(target[CompileInfo], "arguments"):
                srcs = target[CompileInfo].arguments.keys()
                all_files += srcs
                compilation_context = target[CcInfo].compilation_context
                headers = depset(
                    transitive = [headers, compilation_context.headers],
                )
    sources_and_headers = all_files + headers.to_list()
    return sources_and_headers

def _create_wrapper_script(ctx, options, compile_commands_json, config_file):
    options_str = ""
    for item in options:
        options_str += item + " "
    ctx.actions.expand_template(
        template = ctx.file._per_file_script_template,
        output = ctx.outputs.per_file_script,
        is_executable = True,
        substitutions = {
            "{compile_commands_json}": compile_commands_json.path,
            "{codechecker_args}": options_str,
            "{config_file}": config_file.path,
        },
    )

def _per_file_impl(ctx):
    compile_commands_json = _compile_commands_impl(ctx)
    sources_and_headers = _collect_all_sources_and_headers(ctx)
    options = ctx.attr.default_options + ctx.attr.options
    all_files = [compile_commands_json]
    config_file, env_vars = get_config_file(ctx)
    _create_wrapper_script(ctx, options, compile_commands_json, config_file)
    for target in ctx.attr.targets:
        if not CcInfo in target:
            continue
        if CompileInfo in target:
            if hasattr(target[CompileInfo], "arguments"):
                srcs = target[CompileInfo].arguments.keys()
                all_files += srcs
                compilation_context = target[CcInfo].compilation_context
                for src in srcs:
                    args = target[CompileInfo].arguments[src]
                    outputs = _run_code_checker(
                        ctx,
                        src,
                        args,
                        ctx.attr.name,
                        options,
                        config_file,
                        env_vars,
                        compile_commands_json,
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
                compile_info_aspect,
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
    toolchains = ["@rules_python//python:toolchain_type"],
    outputs = {
        "test_script": "%{name}/test_script.sh",
        "per_file_script": "%{name}/per_file_script.py",
    },
    test = True,
)
