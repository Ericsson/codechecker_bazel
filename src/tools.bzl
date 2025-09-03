BUILD_FILE = """
load("@bazel_tools//tools/python:toolchain.bzl", "py_runtime_pair")
load(":defs.bzl", "python3_bin_path", "python2_bin_path")

py_runtime(
    name = "py3_runtime",
    interpreter_path = python3_bin_path,
    python_version = "PY3",
    stub_shebang = "#!" + python3_bin_path,
    visibility = ["//visibility:public"],
)

py_runtime(
    name = "py2_runtime",
    interpreter_path = python2_bin_path,
    python_version = "PY2",
    stub_shebang = "#!" + python2_bin_path,
    visibility = ["//visibility:public"],
)

py_runtime_pair(
    name = "py_runtime_pair",
    py3_runtime = ":py3_runtime",
    py2_runtime = ":py2_runtime" if python2_bin_path != "None" else None,
    visibility = ["//visibility:public"],
)

toolchain(
    name = "python_toolchain",
    toolchain = ":py_runtime_pair",
    toolchain_type = "@bazel_tools//tools/python:toolchain_type",
    visibility = ["//visibility:public"],
)
"""

DEFS_FILE = """
python3_bin_path = "{}"
python2_bin_path = "{}"
"""

def _python_local_repository_impl(repository_ctx):
    repository_ctx.file(
        repository_ctx.path("BUILD"),
        content = BUILD_FILE,
        executable = False,
    )

    python3_bin_path = repository_ctx.which("python3")
    if not python3_bin_path:
        fail("ERROR! python3 is not detected")

    python2_bin_path = repository_ctx.which("python2")
    if not python2_bin_path:
        python2_bin_path = repository_ctx.which("python")

    defs = DEFS_FILE.format(python3_bin_path, python2_bin_path)
    repository_ctx.file(
        repository_ctx.path("defs.bzl"),
        content = defs,
        executable = False,
    )

default_python_tools = repository_rule(
    attrs = {},
    local = True,
    doc = "Generate repository for default python tools",
    implementation = _python_local_repository_impl,
)

def register_default_python_toolchain():
    default_python_tools(name = "default_python_tools")
    native.register_toolchains("@default_python_tools//:python_toolchain")

def _codechecker_local_repository_impl(repository_ctx):
    repository_ctx.file(
        repository_ctx.path("BUILD"),
        content = "",
        executable = False,
    )

    codechecker_bin_path = repository_ctx.which("CodeChecker")
    if not codechecker_bin_path:
        fail("ERROR! CodeChecker is not detected")

    # In future versions use repository_ctx.getenv()
    ccache_disable = repository_ctx.os.environ.get("CCACHE_DISABLE", 0)

    analyzers = repository_ctx.execute([codechecker_bin_path, "analyzers"])

    parsed_analyzers = {}

    lines = analyzers.stdout.strip().split('\n')
    for line in lines:
        parts_dirty = line.split(" ")
        parts = []
        for fragment in parts_dirty:
            if fragment != "":
                parts.append(fragment)
        tool_name = parts[0]
        if 'NOT' not in parts:
            path = parts[1]
            version = parts[2]
            parsed_analyzers[tool_name] = {'path': path, 'version': version}
    bash_bin = repository_ctx.which("bash")
    clang_ccache = repository_ctx.execute(
        [
            bash_bin, "-c",
            "{} -xc -c - --ccache-skip </dev/null".format(
                parsed_analyzers["clangsa"]["path"])]
    )
    gcc_ccache = repository_ctx.execute(
        [
            bash_bin, "-c",
            "{} -xc -c - --ccache-skip </dev/null".format(
                    parsed_analyzers["gcc"]["path"]
                )
        ]
    ) 
    if (clang_ccache.return_code == 0 or gcc_ccache.return_code == 0) and \
        ccache_disable != "1":
        fail("ERROR! ccache detected")

    defs = "CODECHECKER_BIN_PATH = '{}'\n".format(codechecker_bin_path) + \
        "CCACHE_DISABLE = '{}'\n".format(ccache_disable)
    repository_ctx.file(
        repository_ctx.path("defs.bzl"),
        content = defs,
        executable = False,
    )

default_codechecker_tools = repository_rule(
    attrs = {},
    local = True,
    doc = "Generate repository for default CodeChecker tools",
    implementation = _codechecker_local_repository_impl,
)

def register_default_codechecker():
    default_codechecker_tools(name = "default_codechecker_tools")
