# This is bazel rule early prototype for CodeChecker analyze --file
# FIXME: CodeChecker analyze --file --ctu does not currently work

load("@bazel_tools//tools/build_defs/cc:action_names.bzl", "ACTION_NAMES")
load("@bazel_tools//tools/cpp:toolchain_utils.bzl", "find_cpp_toolchain")

CODE_CHECKER_WRAPPER_SCRIPT = """#!/usr/bin/env bash
#set -x
DATA_DIR=$1
shift
CLANG_TIDY_PLIST=$1
shift
CLANGSA_PLIST=$1
shift
LOG_FILE=$1
shift
METADATA=$1
shift
COMPILE_COMMANDS_JSON=$1
shift
COMPILE_COMMANDS_ABS=$COMPILE_COMMANDS_JSON.abs
sed 's|"directory":"."|"directory":"'$(pwd)'"|g' $COMPILE_COMMANDS_JSON > $COMPILE_COMMANDS_ABS
echo "CodeChecker command: $@" $COMPILE_COMMANDS_ABS > $LOG_FILE
echo "===-----------------------------------------------------===" >> $LOG_FILE
echo "                   CodeChecker error log                   " >> $LOG_FILE
echo "===-----------------------------------------------------===" >> $LOG_FILE
eval "$@" $COMPILE_COMMANDS_ABS >> $LOG_FILE 2>&1
# ls -la $DATA_DIR
# NOTE: the following we do to get rid of md5 hash in plist file names
ret_code=$?
echo "===-----------------------------------------------------===" >> $LOG_FILE
if [ $ret_code -eq 1 ] || [ $ret_code -ge 128 ]; then
    echo "===-----------------------------------------------------==="
    echo "[ERROR]: CodeChecker returned with $ret_code!"
    cat $LOG_FILE
    exit 1
fi
cp $DATA_DIR/*_clang-tidy_*.plist $CLANG_TIDY_PLIST
cp $DATA_DIR/*_clangsa_*.plist    $CLANGSA_PLIST
cp $DATA_DIR/metadata.json        $METADATA

# sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" $CLANG_TIDY_PLIST
# sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" $CLANGSA_PLIST

"""

def _run_code_checker(
        ctx,
        src,
        arguments,
        label,
        options,
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
    codechecker_metadata = ctx.actions.declare_file(codechecker_metadata_file_name)

    if "--ctu" in options:
        inputs = [compile_commands_json] + sources_and_headers
    else:
        # NOTE: we collect only headers, so CTU may not work!
        headers = depset([src], transitive = [compilation_context.headers])
        inputs = depset([compile_commands_json, src], transitive = [headers])

    outputs = [
        clang_tidy_plist,
        clangsa_plist,
        codechecker_log,
        codechecker_metadata,
        ]

    # Create CodeChecker wrapper script
    wrapper = ctx.actions.declare_file(ctx.attr.name + "/code_checker.sh")
    ctx.actions.write(
        output = wrapper,
        is_executable = True,
        content = CODE_CHECKER_WRAPPER_SCRIPT,
    )

    # Prepare arguments
    args = ctx.actions.args()

    # NOTE: we pass: data dir, PList and log file names as first 4 arguments
    args.add(data_dir)
    args.add(clang_tidy_plist.path)
    args.add(clangsa_plist.path)
    args.add(codechecker_log.path)
    args.add(codechecker_metadata.path)
    args.add(compile_commands_json.path)
    args.add("CodeChecker")
    args.add("analyze")
    args.add_all(options)
    args.add("--output=" + data_dir)
    args.add("--file=*/" + src.path)

    # Action to run CodeChecker for a file
    ctx.actions.run(
        inputs = inputs,
        outputs = outputs,
        executable = wrapper,
        arguments = [args],
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
            srcs += [src for src in src.files.to_list() if src.is_source and check_valid_file_type(src)]
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
    for attr in ["srcs", "deps", "data", "exports"]:
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
            # FIXME: Create verbose mode, show warning only if thats enabled
            print(
                "Unknown file extension for {} defaulting to c++ compile flags".
                format(src.short_path)
                )
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
    attr_aspects = ["srcs", "deps", "data", "exports"],
    toolchains = ["@bazel_tools//tools/cpp:toolchain_type"],
)

def _compile_commands_json(compile_commands):
    json = "[\n"
    entries = [entry.to_json() for entry in compile_commands]
    json += ",\n".join(entries)
    json += "]\n"
    return json

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

def _per_file_impl(ctx):
    compile_commands_json = _compile_commands_impl(ctx)
    sources_and_headers = _collect_all_sources_and_headers(ctx)
    options = ctx.attr.default_options + ctx.attr.options
    all_files = [compile_commands_json]
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
                        compile_commands_json,
                        compilation_context,
                        sources_and_headers,
                    )
                    all_files += outputs

    # merge metadata
    ctx.actions.expand_template(
        template = ctx.file._metadata_merge_template,
        output = ctx.outputs._metadata_merge_script,
        is_executable = True,
        substitutions = {
            "{PythonPath}": ctx.attr._python_runtime[PyRuntimeInfo].interpreter_path,
        },
    )
    metadata = [file for file in all_files if file.path.endswith("metadata.json")]
    metadata_json = ctx.actions.declare_file(ctx.attr.name + "/data/metadata.json")
    ctx.actions.run(
        inputs = metadata,
        outputs = [metadata_json],
        executable = ctx.outputs._metadata_merge_script,
        arguments = [metadata_json.path] + [file.path for file in metadata],
        mnemonic = "Metadata",
        progress_message = "Merging metadata.json",
    )
    all_files.append(metadata_json)
    ctx.actions.write(
        output = ctx.outputs.test_script,
        is_executable = True,
        content = """
            DATA_DIR=$(dirname {})
            # ls -la $DATA_DIR/data
            # find $DATA_DIR/data -name *.plist -exec sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" {{}} \\;
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
        "_metadata_merge_template": attr.label(
            default = ":metadata_merge.py",
            allow_single_file = True,
        ),
        "_python_runtime": attr.label(
            default = "@default_python_tools//:py3_runtime",
        ),
        "targets": attr.label_list(
            aspects = [
                compile_info_aspect,
            ],
            doc = "List of compilable targets which should be checked.",
        ),
    },
    outputs = {
        "test_script": "%{name}/test_script.sh",
        "_metadata_merge_script": "%{name}/_metadata_merge_script.py"
    },
    test = True,
)

# This interface is deprecated and will be removed
def code_checker_test(
    name,
    targets,
    options = [],
    tags = [],
):
    per_file_test(
        name = name,
        options = options,
        targets = targets,
        tags = tags,
    )
