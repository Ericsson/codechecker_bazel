# cc_binary for simple C++ tests
load(
    "@rules_cc//cc:defs.bzl",
    "cc_binary",
    "cc_library",
)

# codechecker rules
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker",
    "codechecker_config",
    "codechecker_suite",
    "codechecker_test",
)

# Test for strip_include_prefix
cc_library(
    name = "test_inc",
    hdrs = glob(["inc/*.h"]),
    # NOTE: the following is for test purpose only
    # NOTE: use includes instead of strip_include_prefix
    strip_include_prefix = "inc",
)

# Simplest C++ test which should PASS
cc_binary(
    name = "test_pass",
    srcs = ["src/pass.cc"],
    deps = ["test_inc"],
)

# CodeChecker configuration options specification
# based on Bazel configuration approach
codechecker_config(
    name = "codechecker_config",
    analyze = [
        "--disable=profile:default",
        "--enable=core",
        "--enable=bugprone-dangling-handle",
        "--enable=bugprone-fold-init-type",
        "--enable=misc-non-copyable-objects",
        "--report-hash=context-free-v2",
    ],
    # env = CODECHECKER_ENV,
    parse = [
        "--print-step",
    ],
)

# CodeChecker configuration file in JSON format
filegroup(
    name = "codechecker_config_file",
    srcs = [":config.json"],
)

# CodeChecker configuration options specification
# using JSON configuration file based approach,
# inherently supported by CodeChecker
codechecker_config(
    name = "codechecker_config_json",
    config_file = "codechecker_config_file",
)

# Simple codechecker rule - performs only "build" phase without "test"
codechecker(
    name = "codechecker_pass_build",
    config = "codechecker_config_json",
    targets = [
        "test_pass",
    ],
)

# Simplest codechecker_test example
# Runs CodeChecker on "test_pass" target
codechecker_test(
    name = "codechecker_pass",
    analyze = [
        "--ctu",
    ],
    config = "codechecker_config_json",
    targets = [
        "test_pass",
    ],
)

# Simplest codechecker_suite example for "test_pass"
# Can run CodeChecker on targets built for different platforms
# This example performs build for just default platform i.e gcc
codechecker_suite(
    name = "codechecker_pass_multi",
    config = "codechecker_config_json",
    # platforms = [
    #     "@platforms//os:linux",
    #     "@platforms//os:ios",
    #     "@platforms//os:android",
    # ],
    targets = [
        "test_pass",
    ],
)