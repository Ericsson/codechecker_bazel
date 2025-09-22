# Tool filter compile_commands.json file
py_binary(
    name = "compile_commands_filter",
    srcs = ["compile_commands_filter.py"],
    visibility = ["//visibility:public"],
)

# Build & Test script template
exports_files(
    [
        "codechecker_script.py",
        "per_file_script.py",
    ],
)

# The following are flags and default values for clang_tidy_aspect
filegroup(
    name = "clang_tidy_config_default",
    srcs = [],  # empty list: default configuration (.clang-tidy)
)

label_flag(
    name = "clang_tidy_config",
    build_setting_default = ":clang_tidy_config_default",
    visibility = ["//visibility:public"],
)

filegroup(
    name = "clang_tidy_executable_default",
    srcs = [],  # empty list: system clang-tidy
)

label_flag(
    name = "clang_tidy_executable",
    build_setting_default = ":clang_tidy_executable_default",
    visibility = ["//visibility:public"],
)

filegroup(
    name = "clang_tidy_additional_deps_default",
    srcs = [],
)

label_flag(
    name = "clang_tidy_additional_deps",
    build_setting_default = ":clang_tidy_additional_deps_default",
    visibility = ["//visibility:public"],
)
