# cc_binary for simple C++ tests
load(
    "@rules_cc//cc:defs.bzl",
    "cc_binary",
    "cc_library",
)

# clang-tidy and clang -analyze rules
load(
    "@bazel_codechecker//src:clang.bzl",
    "clang_analyze_test",
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

# This simple clang -analyze test should pass
clang_analyze_test(
    name = "clang_analyze_pass",
    options = [
        "-fno-color-diagnostics",  # Example
        # "-Xanalyzer -analyzer-disable-all-checks",
    ],
    targets = [
        "test_pass",
    ],
)

# And this clang -analyze test should fail
# Note "manual" tag (means should not be run with other tests)
clang_analyze_test(
    name = "clang_analyze_fail",
    tags = [
        "manual",
    ],
    targets = [
        "test_pass",
        "test_fail",
    ],
)