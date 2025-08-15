#!/bin/bash
git clone --recurse https://github.com/madler/zlib.git test-proj
cd test-proj
git checkout 5a82f71ed1dfc0bec044d9702463dbdf84ea3b71

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
        ":z",
    ],
)

code_checker_test(
    name = "code_checker_test",
    targets = [
        ":z",
    ],
)

#-------------------------------------------------------
EOF

# Add codechecker_bazel repo to WORKSPACE
cat ../../templates/WORKSPACE.template >> WORKSPACE
