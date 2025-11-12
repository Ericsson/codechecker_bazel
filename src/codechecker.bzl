""" Bazel test rules for CodeChecker """

load(
    "compile_commands.bzl",
    "compile_commands_aspect",
    "compile_commands_impl",
    "platforms_transition",
)
load(
    "@default_codechecker_tools//:defs.bzl",
    "CODECHECKER_BIN_PATH",
    "CCACHE_DISABLE"
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

CodeCheckerConfigInfo = provider(
    doc = "Defines CodeChecker configuration",
    fields = {
        "analyze": "List of arguments for CodeChecker analyze command",
        "parse": "List of arguments for CodeChecker parse command",
        "config_file": "CodeChecker configuration file in JSON format",
        "env": "Environment variables for CodeChecker",
    },
)

def _codechecker_config_impl(ctx):
    return [
        CodeCheckerConfigInfo(
            analyze = ctx.attr.analyze,
            parse = ctx.attr.parse,
            config_file = ctx.attr.config_file,
            env = ctx.attr.env,
        ),
    ]

codechecker_config = rule(
    implementation = _codechecker_config_impl,
    attrs = {
        "analyze": attr.string_list(
            default = [],
            doc = "List of arguments for CodeChecker analyze command",
        ),
        "parse": attr.string_list(
            default = [],
            doc = "List of arguments for CodeChecker parse command",
        ),
        "config_file": attr.label(
            default = None,
            allow_single_file = True,
        ),
        "env": attr.string_list(
            default = [],
            doc = "List of environment variables for CodeChecker",
        ),
    },
)

def _copy_config_to_default(config_file, ctx):
    ctx.actions.run(
        inputs = [config_file],
        outputs = [ctx.outputs.codechecker_config],
        mnemonic = "CopyFile",
        progress_message = "Copying CodeChecker config file",
        executable = "cp",
        arguments = [
            config_file.path,
            ctx.outputs.codechecker_config.path,
        ],
    )

def _codechecker_impl(ctx):
    py_runtime_info = ctx.attr._python_runtime[PyRuntimeInfo]
    python_path = py_runtime_info.interpreter_path

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

    # Have it None by default to avoid overwriting use_default_shell_env
    env_var = {}
    if CCACHE_DISABLE == "1":
        env_var["CCACHE_DISABLE"] = CCACHE_DISABLE

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
        env = env_var,
        # use_default_shell_env = True,
    )

    # Create CodeChecker skip (ignore) file
    ctx.actions.write(
        output = ctx.outputs.codechecker_skipfile,
        content = "\n".join(ctx.attr.skip),
        is_executable = False,
    )

    # Create CodeChecker JSON config file and env vars
    if ctx.attr.config:
        if type(ctx.attr.config) == "list":
            config_info = ctx.attr.config[0][CodeCheckerConfigInfo]
        else:
            config_info = ctx.attr.config[CodeCheckerConfigInfo]
        if config_info.config_file:
            # Create a copy of CodeChecker configuration file
            # provided via codechecker_config(config_file)
            config_file = config_info.config_file.files.to_list()[0]
            _copy_config_to_default(config_file, ctx)
        else:
            # Create CodeChecker configuration file in JSON format
            # from Bazel codechecker_config(analyze, parse)
            config_json = {}
            if config_info.analyze:
                config_json["analyze"] = config_info.analyze
            if config_info.parse:
                config_json["parse"] = config_info.parse
            config_content = json.encode_indent(config_json)
            ctx.actions.write(
                output = ctx.outputs.codechecker_config,
                content = config_content,
                is_executable = False,
            )

        # Pack env vars for CodeChecker
        codechecker_env = "; ".join(config_info.env)
    else:
        # Empty CodeChecker JSON config file
        ctx.actions.write(
            output = ctx.outputs.codechecker_config,
            content = "{}",
            is_executable = False,
        )
        codechecker_env = ""

    codechecker_files = ctx.actions.declare_directory(ctx.label.name + "/codechecker-files")
    ctx.actions.expand_template(
        template = ctx.file._codechecker_script_template,
        output = ctx.outputs.codechecker_script,
        is_executable = True,
        substitutions = {
            "{Mode}": "Run",
            "{Verbosity}": "DEBUG",
            "{PythonPath}": python_path,
            "{codechecker_bin}": CODECHECKER_BIN_PATH,
            "{compile_commands}": ctx.outputs.codechecker_commands.path,
            "{codechecker_skipfile}": ctx.outputs.codechecker_skipfile.path,
            "{codechecker_config}": ctx.outputs.codechecker_config.path,
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
                ctx.outputs.codechecker_config,
            ] + source_files,
        ),
        outputs = [
            codechecker_files,
            ctx.outputs.codechecker_log,
        ],
        executable = ctx.outputs.codechecker_script,
        arguments = [],
        mnemonic = "CodeChecker",
        progress_message = "CodeChecker %s" % str(ctx.label),
        env = env_var,
        # use_default_shell_env = True,
    )

    # List all files required at build and run (test) time
    all_files = [
        ctx.outputs.compile_commands,
        ctx.outputs.codechecker_commands,
        ctx.outputs.codechecker_skipfile,
        ctx.outputs.codechecker_config,
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
        "_python_runtime": attr.label(
            default = "@default_python_tools//:py3_runtime",
        ),
    },
    outputs = {
        "compile_commands": "%{name}/compile_commands.json",
        "codechecker_commands": "%{name}/codechecker_commands.json",
        "codechecker_skipfile": "%{name}/codechecker_skipfile.cfg",
        "codechecker_config": "%{name}/codechecker_config.json",
        "codechecker_script": "%{name}/codechecker_script.py",
        "codechecker_log": "%{name}/codechecker.log",
    },
)

def _codechecker_test_impl(ctx):
    py_runtime_info = ctx.attr._python_runtime[PyRuntimeInfo]
    python_path = py_runtime_info.interpreter_path

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
            "{PythonPath}": python_path,
            "{codechecker_bin}": CODECHECKER_BIN_PATH,
            "{codechecker_files}": codechecker_files.short_path,
            "{Severities}": " ".join(ctx.attr.severities),
        },
    )

    # Return test script and all required files
    run_files = default_runfiles + [ctx.outputs.codechecker_test_script]
    return [
        DefaultInfo(
            files = depset(all_files),
            runfiles = ctx.runfiles(files = run_files),
            executable = ctx.outputs.codechecker_test_script,
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
        "_whitelist_function_transition": attr.label(
            default = "@bazel_tools//tools/whitelists/function_transition_whitelist",
            doc = "needed for transitions",
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
        "_python_runtime": attr.label(
            default = "@default_python_tools//:py3_runtime",
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
    },
    outputs = {
        "compile_commands": "%{name}/compile_commands.json",
        "codechecker_commands": "%{name}/codechecker_commands.json",
        "codechecker_skipfile": "%{name}/codechecker_skipfile.cfg",
        "codechecker_config": "%{name}/codechecker_config.json",
        "codechecker_script": "%{name}/codechecker_script.py",
        "codechecker_log": "%{name}/codechecker.log",
        "codechecker_test_script": "%{name}/codechecker_test_script.py",
    },
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
