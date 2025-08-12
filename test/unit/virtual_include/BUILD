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

# Test for strip_include_prefix
cc_library(
    name = "test_inc",
    hdrs = glob(["inc/*.h"]),
    # NOTE: the following is for test purpose only
    # NOTE: use includes instead of strip_include_prefix
    strip_include_prefix = "inc",
)

# Simplest C++ test which should FAIL
cc_binary(
    name = "virtual_include",
    srcs = ["source.cc"],
    deps = ["test_inc"],
)

# Simplest virtual include resolution test
codechecker_test(
    name = "codechecker_virtual_include",
    tags = [
        "manual",
    ],
    targets = [
        "virtual_include",
    ],
)

code_checker_test(
    name = "code_checker_virtual_include",
    tags = [
        "manual",
    ],
    targets = [
        "virtual_include",
    ]
)
