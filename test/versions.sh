#!/usr/bin/env bash

PYTHON_VERSION="$(python3 --version)"
BAZEL_VERSION="$(bazel --version)"
CODECHECKER_VERSION="CodeChecker $(CodeChecker version | grep -m 1 -Po '(?<=package version \| ).*')"
echo "Versions: $PYTHON_VERSION, $BAZEL_VERSION, $CODECHECKER_VERSION"
