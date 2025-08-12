# cc_binary for simple C++ tests
load(
    "@rules_cc//cc:defs.bzl",
    "cc_binary",
    "cc_library",
)

# compile_commands rule
load(
    "@bazel_codechecker//src:compile_commands.bzl",
    "compile_commands",
)

# codechecker rules
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker",
    "codechecker_config",
    "codechecker_suite",
    "codechecker_test",
)

# clang-tidy and clang -analyze rules
load(
    "@bazel_codechecker//src:clang.bzl",
    "clang_analyze_test",
    "clang_tidy_test",
)

# clang -analyze + CTU rule
load(
    "@bazel_codechecker//src:clang_ctu.bzl",
    "clang_ctu_test",
)

# Prototype for CodeChecker analyze --file
# NOTE: CodeChecker analyze --file --ctu does not work
load(
    "@bazel_codechecker//src:code_checker.bzl",
    "code_checker_test",
)

# Test defect in CTU mode
cc_library(
    name = "linking",
    hdrs = ["linking.h"],
)

# Test defect in CTU mode
cc_library(
    name = "secondary",
    srcs = ["secondary.cc"],
    deps = ["linking"],
)

# Simplest C++ test which should PASS
cc_binary(
    name = "primary",
    srcs = ["primary.cc"],
    deps = [
        "secondary",
        "linking"
    ],
)

code_checker_test(
    name = "code_checker_caching",
    targets = [
        "primary",
    ],
)
