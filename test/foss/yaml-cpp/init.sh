#!/bin/bash
git clone --recurse https://github.com/jbeder/yaml-cpp.git test-proj
cd test-proj
git checkout yaml-cpp-0.7.0

# This file must be in the root of the project to be analyzed for bazelisk to work
cp ../../templates/.bazelversion ./.bazelversion

# Add codechecker to the project
cat <<EOF >> BUILD.bazel
#-------------------------------------------------------

# codechecker rules
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker_test",
)
load(
    "@bazel_codechecker//src:code_checker.bzl",
    "code_checker_test",
)


codechecker_test(
    name = "codechecker_test",
    targets = [
        ":yaml-cpp",
    ],
)

code_checker_test(
    name = "code_checker_test",
    targets = [
        ":yaml-cpp",
    ],
)

#-------------------------------------------------------
EOF

# Add codechecker_bazel repo to WORKSPACE
cat ../../templates/WORKSPACE.template >> WORKSPACE