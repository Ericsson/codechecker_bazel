load("@bazel_tools//tools/build_defs/cc:action_names.bzl", "ACTION_NAMES")
load("@bazel_tools//tools/cpp:toolchain_utils.bzl", "find_cpp_toolchain")

CLANG_CTU_WRAPPER_SCRIPT = """#!/usr/bin/env bash
#set -x
REPORT_TYPE=$1
shift
REPORT_FILE=$1
shift
LOG_FILE=$1
shift
CTU_DIR=$1
shift
ANALYZE_FLAGS=$1
shift
SRC_FILE=$1
shift
CC_FLAGS=$@

[[ $REPORT_TYPE = "html" ]] && mkdir -p $REPORT_FILE
[[ $REPORT_TYPE = "text" ]] && REPORT=" 2>&1 | tee $REPORT_FILE"
COMMAND="clang --analyze $ANALYZE_FLAGS \
  -Xclang -analyzer-output=$REPORT_TYPE -o $REPORT_FILE \
  -Xclang -analyzer-config -Xclang experimental-enable-naive-ctu-analysis=true \
  -Xclang -analyzer-config -Xclang ctu-dir=$CTU_DIR \
  $CC_FLAGS \
  $SRC_FILE \
  $REPORT"

echo "Running: $COMMAND" > $LOG_FILE
echo "==================================" >> $LOG_FILE
eval "$COMMAND" 2>&1 | tee -a $LOG_FILE
"""

def _run_clang_ctu(
        ctx,
        src,
        arguments,
        label,
        options,
        ast_files,
        def_files,
        sources_and_headers):
    # Report type (html|plist|plist-multi-file|plist-html|sarif|sarif-html|text)
    report_type = "text"

    # Creating externalDefMap.txt file
    def_file_name = label + "/externalDefMap.txt"
    def_file = ctx.actions.declare_file(def_file_name)
    ctx.actions.run_shell(
        outputs = [def_file],
        inputs = def_files + ast_files,
        command = "cat {} > {}".format(
            " ".join([f.path for f in def_files]),
            def_file.path,
        ),
        use_default_shell_env = True,  # FIXME: we should not use this
    )

    # Extension of the report file/dir
    if report_type in ["plist", "plist-multi-file", "plist-html"]:
        report_extension = "plist"
    elif report_type == "text":
        report_extension = "txt"
    elif report_type in ["sarif", "sarif-html"]:
        report_extension = "json"
    else:
        report_extension = report_type

    # Define output file names
    report_file_name = "{}/{}.{}".format(label, src.short_path, report_extension)
    log_file_name = "{}/{}.log".format(label, src.short_path)

    # Declare output files
    if report_type == "html":
        report_file = ctx.actions.declare_directory(report_file_name)
    else:
        report_file = ctx.actions.declare_file(report_file_name)
    log_file = ctx.actions.declare_file(log_file_name)

    inputs = sources_and_headers + ast_files + [def_file]
    outputs = [report_file, log_file]

    # Create CodeChecker wrapper script
    wrapper = ctx.actions.declare_file(label + "/clang_ctu.sh")
    ctx.actions.write(
        output = wrapper,
        is_executable = True,
        content = CLANG_CTU_WRAPPER_SCRIPT,
    )

    # Prepare arguments
    args = ctx.actions.args()
    args.add(report_type)
    args.add(report_file.path)
    args.add(log_file.path)
    args.add(def_file.dirname)  # ctu-dir
    args.add(" ".join(options))
    args.add(src.path)
    args.add_all(arguments)

    # Action to run CodeChecker for a file
    ctx.actions.run(
        inputs = inputs,
        outputs = outputs,
        executable = wrapper,
        arguments = [args],
        mnemonic = "ClangCTU",
        use_default_shell_env = True,
        progress_message = "clang -analyze +CTU {}".format(src.short_path),
    )
    return outputs

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
            srcs += [src for src in src.files.to_list() if src.is_source and check_valid_file_type(src)]
    return srcs

def _toolchain_flags(ctx, action_name, with_compiler = False):
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
    if not with_compiler:
        return flags
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
    # Remove them here, to allow users to run analysis, without having
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
    sources = depset(sources).to_list()  # Remove duplicates
    return sources

def _compile_info_aspect_impl(target, ctx):
    compilation_context = target[CcInfo].compilation_context

    rule_flags = ctx.rule.attr.copts if hasattr(ctx.rule.attr, "copts") else []
    c_flags = _safe_flags(_toolchain_flags(ctx, ACTION_NAMES.c_compile) + rule_flags)  # + ["-xc"]
    cxx_flags = _safe_flags(_toolchain_flags(ctx, ACTION_NAMES.cpp_compile) + rule_flags)  # + ["-xc++"]

    srcs = _collect_all_sources(ctx)

    compile_args = _compile_args(compilation_context)
    arguments = {}
    for src in srcs:
        flags = c_flags if src.extension in ["c", "C"] else cxx_flags
        arguments[src] = flags + compile_args  # + [src.path]
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

def _generate_ast_and_def_files(ctx, target, all_sources):
    if not CcInfo in target:
        return ([], [])
    if CompileInfo not in target:
        return ([], [])
    if not hasattr(target[CompileInfo], "arguments"):
        return ([], [])
    ast_files = []
    def_files = []
    srcs = target[CompileInfo].arguments.keys()
    for src in srcs:
        args = target[CompileInfo].arguments[src]
        file_path = ctx.label.name + "." + target.label.name + "/" + src.path

        # clang $CCFLAGS $FILEPATH -emit-ast -D__clang_analyzer__ -w -o $AST_FILE
        ast_file = ctx.actions.declare_file(file_path + ".ast")
        ctx.actions.run_shell(
            inputs = all_sources,
            outputs = [ast_file],
            # NOTE: realpath!
            command = "clang {} $(realpath {}) {} -o {}".format(
                " ".join(args),
                src.path,
                "-emit-ast -D__clang_analyzer__ -w",
                ast_file.path,
            ),
            use_default_shell_env = True,  # FIXME: we should not use this
        )
        ast_files.append(ast_file)

        # clang-extdef-mapping $FILEPATH -- $CCFLAGS > $DEF_FILE
        # sed -i -e "s|$(pwd)/$FILEPATH|$FILENAME.ast|g" $DEF_FILE
        def_file = ctx.actions.declare_file(file_path + ".def")
        command = """
        clang-extdef-mapping {} -- {} > {}
        sed -i -e "s| /\\S*{}| {}|g" {}
        """  # FIXME: how to match absolute path?
        ctx.actions.run_shell(
            inputs = all_sources + [ast_file],
            outputs = [def_file],
            command = command.format(
                src.path,
                " ".join(args),
                def_file.path,
                src.short_path,
                src.short_path + ".ast",
                def_file.path,
            ),
            use_default_shell_env = True,  # FIXME: we should not use this
        )
        def_files.append(def_file)
    return (ast_files, def_files)

def _collect_all_sources_and_headers(ctx):
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

def _clang_ctu_impl(ctx):
    sources_and_headers = _collect_all_sources_and_headers(ctx)
    all_files = sources_and_headers
    options = ctx.attr.default_options + ctx.attr.options
    for target in ctx.attr.targets:
        if not CcInfo in target:
            continue
        if CompileInfo not in target:
            continue
        if not hasattr(target[CompileInfo], "arguments"):
            continue
        ast_files, def_files = _generate_ast_and_def_files(ctx, target, sources_and_headers)
        all_files += ast_files + def_files
        srcs = target[CompileInfo].arguments.keys()
        all_files += srcs
        for src in srcs:
            args = target[CompileInfo].arguments[src]
            outputs = _run_clang_ctu(
                ctx,
                src,
                args,
                ctx.attr.name + "." + target.label.name,
                options,
                ast_files,
                def_files,
                sources_and_headers,
            )
            all_files += outputs
    reports = " ".join([f.short_path for f in all_files if f.extension == "txt"])
    ctx.actions.write(
        output = ctx.outputs.test_script,
        is_executable = True,
        content = """
            reports="{}"
            exit_code=0
            for f in $reports; do
                echo -n $f
                if [ -s $f ]; then
                    echo " - FAIL!"
                    exit_code=1
                else
                    echo " - PASS"
                fi
            done
            for f in $reports; do
                if [ -s $f ]; then
                    echo "-----------------------------------------------------------------------------"
                    echo $f
                    echo "-----------------------------------------------------------------------------"
                    cat $f
                fi
            done
            exit $exit_code
        """.format(reports),
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

clang_ctu_test = rule(
    implementation = _clang_ctu_impl,
    attrs = {
        "options": attr.string_list(
            default = [],
            doc = "List of clang --analyze options",
        ),
        "default_options": attr.string_list(
            default = [
                "-fcolor-diagnostics",
                # "-Xclang -analyzer-config -Xclang display-ctu-progress=true",
            ],
            # Use: clang -cc1 -analyzer-config-help
            doc = "List of default analyze options",
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
    },
    test = True,
)
