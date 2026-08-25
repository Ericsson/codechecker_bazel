"""
This file provides the toolchain rule for CodeChecker
"""

CodeCheckerInfo = provider(
    doc = "This provider provides the executable path for CodeChecker and its related tools",
    fields = {
        "clang_tidy": "clang-tidy executable",
        "clangsa": "Clang executable",
        "codechecker": "CodeChecker executable",
        "fake_path": "A File in the fake PATH directory. Use .dirname to get the directory path.",
        "runfiles": "Depset of files needed to run the tools: the three executables, " +
                    "fake PATH contents, plus their transitive data_runfiles. Pass to " +
                    "`tools` in ctx.actions.run and include in test runfiles.",
    },
)

def _codechecker_toolchain_impl(ctx):
    fake_path_dir = "fake_path"
    dirname = ctx.actions.declare_file(fake_path_dir + "/dirname")
    ctx.actions.symlink(
        output = dirname,
        target_file = ctx.executable.dirname,
    )

    fake_path_files = [dirname]

    runfiles = depset(
        direct = [
            ctx.executable.codechecker,
            ctx.executable.clangsa,
            ctx.executable.clang_tidy,
        ] + fake_path_files,
        transitive = [
            # We also collect files necessary for these programs to run.
            # Those files should be declared with `data = [...]`
            # in the executable's target.
            ctx.attr.codechecker[DefaultInfo].data_runfiles.files,
            ctx.attr.clangsa[DefaultInfo].data_runfiles.files,
            ctx.attr.clang_tidy[DefaultInfo].data_runfiles.files,
        ],
    )
    toolchain_info = platform_common.ToolchainInfo(
        codecheckerinfo = CodeCheckerInfo(
            codechecker = ctx.executable.codechecker,
            clang_tidy = ctx.executable.clang_tidy,
            clangsa = ctx.executable.clangsa,
            fake_path = dirname,
            runfiles = runfiles,
        ),
    )
    return [
        toolchain_info,
        DefaultInfo(files = depset(fake_path_files)),
    ]

codechecker_toolchain = rule(
    implementation = _codechecker_toolchain_impl,
    attrs = {
        "clang_tidy": attr.label(
            default = "@default_codechecker_tools//:clang_tidy",
            doc = "Executable target for `clang-tidy`.",
            executable = True,
            cfg = "exec",
        ),
        "clangsa": attr.label(
            default = "@default_codechecker_tools//:clang",
            doc = "Executable target for `clang`, used for Clang Static Analyzer.",
            executable = True,
            cfg = "exec",
        ),
        "codechecker": attr.label(
            default = "@default_codechecker_tools//:CodeChecker",
            doc = "Executable target for `CodeChecker`.",
            executable = True,
            cfg = "exec",
        ),
        "dirname": attr.label(
            default = "@default_codechecker_tools//:dirname",
            doc = "Executable target for dirname",
            executable = True,
            cfg = "exec",
        ),
    },
)
