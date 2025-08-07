# cc_binary for simple C++ tests
load(
    "@rules_cc//cc:defs.bzl",
    "cc_binary",
    "cc_library",
)

# codechecker rules
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker_test",
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

# Test defect in transitive dependencies
cc_library(
    name = "test_lib",
    srcs = ["src/lib.cc"],
)

# Test defect in CTU mode
cc_library(
    name = "test_ctu",
    srcs = ["src/ctu.cc"],
)

# Simplest C++ test which should PASS
cc_binary(
    name = "test_pass",
    srcs = ["src/pass.cc"],
    deps = ["test_inc"],
)

# Simplest C++ test which should FAIL
cc_binary(
    name = "test_fail",
    srcs = ["src/fail.cc"],
    deps = [
        "test_ctu",
        "test_inc",
        "test_lib",
    ],
)

# This codechecker_test CTU example supposed to fail showing findings report
# Note "manual" tag (means should not be run with other tests)
codechecker_test(
    name = "codechecker_ctu",
    analyze = [
        "--ctu",
    ],
    tags = [
        "manual",
    ],
    targets = [
        "test_fail",
    ],
)

# FIXME: The following test does not detect CTU problem
# CodeChecker analyze --file --ctu does not work
code_checker_test(
    name = "code_checker_ctu",
    options = [
        "--ctu",
    ],
    tags = [
        "manual",
    ],
    targets = [
        "test_pass",
        "test_fail",
    ],
)

# This simple clang -analyze + CTU test should pass
clang_ctu_test(
    name = "clang_ctu_pass",
    targets = [
        "test_pass",
    ],
)

# And this clang -analyze + CTU test should fail
# Note "manual" tag (means should not be run with other tests)
clang_ctu_test(
    name = "clang_ctu_fail",
    options = [
        # "-fno-color-diagnostics",  # Example
        # "-Xanalyzer -analyzer-disable-all-checks",
    ],
    tags = [
        "manual",
    ],
    targets = [
        "test_pass",
        "test_fail",
    ],
)