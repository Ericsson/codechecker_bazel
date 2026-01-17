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
Rulesets for running clang-tidy and the clang static analyzer.
"""

load("@bazel_tools//tools/build_defs/cc:action_names.bzl", "ACTION_NAMES")
load("@bazel_tools//tools/cpp:toolchain_utils.bzl", "find_cpp_toolchain")
load("compile_commands.bzl", "platforms_transition")
load("common.bzl", "SOURCE_ATTR", "version_specific_attributes")

CLANG_TIDY_WRAPPER_SCRIPT = """#!/usr/bin/env bash
OUTPUT=$1
shift

# Make sure the output exists, and empty if there are no errors,
# (clang-tidy doesn't create a patch file if there are no errors).
touch $OUTPUT

# echo "$@"
$@
"""

CLANG_ANALYZE_WRAPPER_SCRIPT = """#!/usr/bin/env bash
# echo "$@"
$@
"""

def _run_tidy(
        ctx,
        exe,
        config,
        options,
        headers,
        infile,
        arguments,
        label,
        additional_deps = None):
    # Specify the output file
    outfile = ctx.actions.declare_file(
        label + "." + infile.path + ".clang-tidy.yaml",
    )

    # Define which clang-tidy to run
    if exe and exe.files.to_list():
        clang_tidy_bin = exe.files_to_run.executable
    else:
        clang_tidy_bin = "clang-tidy"

    # If config file is from a filegroup
    if config and hasattr(config, "files"):
        config = config.files.to_list()[0]
    # Create clang-tidy config file
    if not config:
        config = ctx.actions.declare_file(label + ".clang_tidy_config.yaml")
        ctx.actions.write(output = config, content = "")

    # Create clang-tidy wrapper script
    wrapper = ctx.actions.declare_file(label + ".clang_tidy.sh")
    ctx.actions.write(
        output = wrapper,
        is_executable = True,
        content = CLANG_TIDY_WRAPPER_SCRIPT,
    )

    # Prepare arguments
    args = ctx.actions.args()

    # NOTE: we pass output file first and also as an argument below
    args.add(outfile.path)

    # Add clang-tidy binary
    args.add(clang_tidy_bin)

    # Add config file
    args.add("--config-file=" + config.path)

    # Add output file
    args.add("--export-fixes=" + outfile.path)

    # Add clang-tidy options
    if options:
        args.add_all(options)

    # Add source file to check
    args.add(infile.path)

    # Start args passed to the compiler
    args.add("--")

    # Add compiler flags -I -D etc
    args.add_all(arguments)

    input_files = [infile]
    if config:
        input_files.append(config)
    if exe and exe.files_to_run.executable:
        input_files.append(exe.files_to_run.executable)
    if additional_deps:
        input_files.extend(additional_deps.files.to_list())
    inputs = depset(
        direct = input_files,
        transitive = [headers],
    )
    ctx.actions.run(
        inputs = inputs,
        outputs = [outfile],
        executable = wrapper,
        arguments = [args],
        mnemonic = "ClangTidy",
        use_default_shell_env = True,
        progress_message = "Run clang-tidy on {}".format(infile.short_path),
    )
    return outfile

def _run_analyzer(
        ctx,
        exe,
        config,
        options,
        headers,
        infile,
        arguments,
        label,
        additional_deps = None):
    # Specify the output file
    outfile = ctx.actions.declare_file(
        label + "." + infile.path + ".clang-analyze.plist",
    )

    # Define which clang to run
    if exe and exe.files.to_list():
        clang_bin = exe.files_to_run.executable
    else:
        clang_bin = "clang"

    # Create config file? FIXME: why do we need this?
    if not config:
        config = ctx.actions.declare_file(label + ".clang_analyze_config.txt")
        ctx.actions.write(
            output = config,
            content = "",
        )

    # Create clang -analyze wrapper script
    wrapper = ctx.actions.declare_file(label + ".clang-analyze.sh")
    ctx.actions.write(
        output = wrapper,
        is_executable = True,
        content = CLANG_ANALYZE_WRAPPER_SCRIPT,
    )

    # Prepare arguments
    args = ctx.actions.args()

    # Add clang binary
    args.add(clang_bin)

    # # Add config file
    # args.add(config.path)

    # Mandatory Clang Analyze options
    args.add("--analyze")
    args.add("-Xclang")
    args.add("-analyzer-output=plist-multi-file")

    # Add clang options
    if options:
        args.add_all(options)

    # Add source file to check
    args.add(infile.path)

    # Add compiler flags -I -D etc
    args.add_all(arguments)

    # Add output file
    args.add("-o")
    args.add(outfile.path)

    input_files = [infile]
    if config:
        input_files.append(config)
    if exe and exe.files_to_run.executable:
        input_files.append(exe.files_to_run.executable)
    if additional_deps:
        input_files.extend(additional_deps.files.to_list())
    inputs = depset(
        direct = input_files,
        transitive = [headers],
    )
    ctx.actions.run(
        inputs = inputs,
        outputs = [outfile],
        executable = wrapper,
        arguments = [args],
        mnemonic = "ClangAnalyzer",
        use_default_shell_env = True,
        progress_message = "Run clang --analyze on {}".format(infile.short_path),
    )
    return outfile

def check_valid_file_type(src):
    """
    Returns True if the file type matches one of the permitted
    srcs file types for C and C++ header/source files.
    """
    permitted_file_types = [
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".c++",
        ".C",
        ".h",
        ".hh",
        ".hpp",
        ".hxx",
        ".inc",
        ".inl",
        ".H",
    ]
    for file_type in permitted_file_types:
        if src.basename.endswith(file_type):
            return True
    return False

def _rule_sources(ctx):
    srcs = []
    if hasattr(ctx.rule.attr, "srcs"):
        for src in ctx.rule.attr.srcs:
            for file in src.files.to_list():
                if file.is_source and check_valid_file_type(file):
                    srcs.append(file)
    return srcs

def _toolchain_flags(ctx, action_name = ACTION_NAMES.cpp_compile):
    cc_toolchain = find_cpp_toolchain(ctx)
    feature_configuration = cc_common.configure_features(
        ctx = ctx,
        cc_toolchain = cc_toolchain,
    )
    compile_variables = cc_common.create_compile_variables(
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        user_compile_flags = ctx.fragments.cpp.cxxopts + ctx.fragments.cpp.copts,
    )
    flags = cc_common.get_memory_inefficient_command_line(
        feature_configuration = feature_configuration,
        action_name = action_name,
        variables = compile_variables,
    )
    compiler = cc_common.get_tool_for_action(
        feature_configuration = feature_configuration,
        action_name = action_name,
    ).split("/")[-1]
    return flags + ["--driver-mode=" + compiler]

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
        "-analyze-and-compile",
        "-O3",
        "-O4",
    ]

    return [flag for flag in flags if flag not in unsupported_flags]

def _valid_for_clang_tidy(target, ctx):
    # if not a C/C++ target, we are not interested
    if not CcInfo in target:
        return False

    # Ignore external targets
    if target.label.workspace_root.startswith("external"):
        return False

    # Targets with specific tags will not be formatted
    ignore_tags = [
        "noclangtidy",
        "no-clang-tidy",
    ]
    for tag in ignore_tags:
        if tag in ctx.rule.attr.tags:
            return False
    return True

CompileInfo = provider(
    doc = "Source files and corresponding compilation arguments",
    fields = {
        "arguments": "dict: file -> list of arguments",
        "headers": "list: header files",
    },
)

def _process_all_deps(ctx, arguments, headers):
    for attr in SOURCE_ATTR:
        if hasattr(ctx.rule.attr, attr):
            deps = getattr(ctx.rule.attr, attr)
            for dep in deps:
                if CompileInfo in dep:
                    if hasattr(dep[CompileInfo], "arguments"):
                        arguments.update(dep[CompileInfo].arguments)
                    if hasattr(dep[CompileInfo], "headers"):
                        headers += dep[CompileInfo].headers.to_list()

    # # NOTE: Alternative implementation
    # for attr in dir(ctx.rule.attr):
    #     deps = getattr(ctx.rule.attr, attr)
    #     if type(deps) == "list":
    #         for dep in deps:
    #             if type(dep) == "Target" and CompileInfo in dep:
    #                 if hasattr(dep[CompileInfo], "arguments"):
    #                     arguments.update(dep[CompileInfo].arguments)
    #                 if hasattr(dep[CompileInfo], "headers"):
    #                     headers += dep[CompileInfo].headers.to_list()

def _get_sources(ctx):
    sources = _rule_sources(ctx)
    arguments = { src: [] for src in sources }
    headers = []
    _process_all_deps(ctx, arguments, headers)
    return arguments.keys()

def _compile_info_aspect_impl(target, ctx):
    arguments = {}
    headers = []
    _process_all_deps(ctx, arguments, headers)

    if _valid_for_clang_tidy(target, ctx):
        compilation_context = target[CcInfo].compilation_context
        headers += compilation_context.headers.to_list()
        rule_flags = ctx.rule.attr.copts if hasattr(ctx.rule.attr, "copts") else []
        c_flags = _safe_flags(_toolchain_flags(ctx, ACTION_NAMES.c_compile) + rule_flags)  # + ["-xc"]
        cxx_flags = _safe_flags(_toolchain_flags(ctx, ACTION_NAMES.cpp_compile) + rule_flags)  # + ["-xc++"]
        srcs = _get_sources(ctx)
        compile_args = _compile_args(compilation_context)
        for src in srcs:
            flags = c_flags if src.extension in ["c", "C"] else cxx_flags
            arguments[src] = compile_args + flags

    return [
        CompileInfo(
            arguments = arguments,
            headers = depset(headers),
        ),
    ]

compile_info_aspect = aspect(
    implementation = _compile_info_aspect_impl,
    fragments = ["cpp"],
    attr_aspects = SOURCE_ATTR,
    toolchains = ["@bazel_tools//tools/cpp:toolchain_type"],
    attrs = {
        "_cc_toolchain": attr.label(default = Label("@bazel_tools//tools/cpp:current_cc_toolchain")),
    },
)

def _clang_test(ctx, tool):
    all_files = []
    all_headers = depset()
    for target in ctx.attr.targets:
        if CompileInfo in target:
            if hasattr(target[CompileInfo], "arguments"):
                srcs = target[CompileInfo].arguments.keys()
                headers = target[CompileInfo].headers
                all_files += srcs
                for src in srcs:
                    arguments = target[CompileInfo].arguments[src]
                    report = tool(
                        ctx,
                        ctx.attr.executable,
                        ctx.attr.config_file,
                        ctx.attr.default_options + ctx.attr.options,
                        headers,
                        src,
                        arguments,
                        ctx.attr.name,
                    )
                    all_files.append(report)
                    all_headers = depset(transitive = [all_headers, headers])

    ctx.actions.write(
        output = ctx.outputs.test_script,
        is_executable = True,
        content = "true",
    )
    files = depset(
        direct = all_files,
        transitive = [all_headers],
    )
    run_files = [ctx.outputs.test_script] + files.to_list()
    return [
        DefaultInfo(
            files = files,
            runfiles = ctx.runfiles(files = run_files),
            executable = ctx.outputs.test_script,
        ),
    ]

def _clang_tidy_test_impl(ctx):
    return _clang_test(ctx, _run_tidy)

clang_tidy_test = rule(
    implementation = _clang_tidy_test_impl,
    attrs = {
        "platform": attr.string(
            default = "",  #"@platforms//os:linux",
            doc = "Platform to build for",
        ),
        "targets": attr.label_list(
            aspects = [
                compile_info_aspect,
            ],
            cfg = platforms_transition,
            doc = "List of compilable targets which should be checked.",
        ),
        "options": attr.string_list(
            default = [],
            doc = "List of clang-tidy options, e.g.: --checks=",
        ),
        "default_options": attr.string_list(
            default = [
                "--quiet",
                "--use-color",
                "--warnings-as-errors=*",
                # "--header-filter=.*",
                # "--checks=bugprone-*,cppcoreguidelines-*,google-*,performance-*",
            ],
            doc = "List of default clang-tidy options",
        ),
        "config_file": attr.label(
            default = None,
            allow_single_file = True,
            doc = "Clang-tidy config file (usually .clang-tidy)",
        ),
        "executable": attr.label(
            default = None,
            allow_single_file = True,
            executable = True,
            cfg = "exec",
            doc = "Clang-tidy executable",
        ),
    } | version_specific_attributes(),
    outputs = {
        "test_script": "%{name}.test_script.sh",
    },
    test = True,
)

def _clang_analyze_test_impl(ctx):
    return _clang_test(ctx, _run_analyzer)

clang_analyze_test = rule(
    implementation = _clang_analyze_test_impl,
    attrs = {
        "platform": attr.string(
            default = "",  #"@platforms//os:linux",
            doc = "Platform to build for",
        ),
        "targets": attr.label_list(
            aspects = [
                compile_info_aspect,
            ],
            cfg = platforms_transition,
            doc = "List of compilable targets which should be checked.",
        ),
        "options": attr.string_list(
            default = [],
            doc = "List of clang options, e.g.: -fcolor-diagnostics",
        ),
        "default_options": attr.string_list(
            default = [
                "-fcolor-diagnostics",
                "-Qunused-arguments",
                "-Xanalyzer -analyzer-werror",
                "-Xclang -analyzer-opt-analyze-headers",
                "-Xclang -analyzer-config -Xclang expand-macros=true",
                "-Xclang -analyzer-config -Xclang aggressive-binary-operation-simplification=true",
                "-Xclang -analyzer-config -Xclang crosscheck-with-z3=true",
                # "-Xclang -analyzer-config -Xclang experimental-enable-naive-ctu-analysis=true",
                # "-Xclang -analyzer-config -Xclang ctu-dir=.../data/ctu-dir/${platform}",
                # "-Xclang -analyzer-config -Xclang display-ctu-progress=true",
            ],
            doc = "List of default clang options",
        ),
        "config_file": attr.label(
            default = None,
            allow_single_file = True,
            doc = "?",  # FIXME: configuration file for clang -analyze?
        ),
        "executable": attr.label(
            default = None,
            allow_single_file = True,
            executable = True,
            cfg = "exec",
            doc = "Clang executable",
        ),
    } | version_specific_attributes(),
    outputs = {
        "test_script": "%{name}.test_script.sh",
    },
    test = True,
)
