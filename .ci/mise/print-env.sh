#!/usr/bin/env bash

set -eE  # -E ensures ERR traps are inherited by functions/subshells

VERBOSE_FLAG=$( [[ " $@ " =~ " -vvv " ]] && echo "-vvv" || echo "" )

failure_handler() {
    local exit_code=$1
    local line_no=$2
    local command=$3
    echo "--- ERROR REPORT ---"
    echo "Failed Command: $command"
    echo "Exit Code: $exit_code"
    echo "Line Number: $line_no"
    echo "--------------------"
    exit "$exit_code"
}
# Pass the last exit code, line number, and exact command string
if [[ -n "$VERBOSE_FLAG" ]]; then
    trap 'failure_handler $? $LINENO "$BASH_COMMAND"' ERR
fi

PYTHON_VERSION="$(python3 --version)"
BAZEL_VERSION="$(bazel --version)"
CODECHECKER_VERSION="CodeChecker $(CodeChecker version | grep -m 1 -Po '(?<=package version \| ).*' | xargs)"
CLANG_VERSION="clang $(clang --version  | grep -m 1 -Po '(?<=version ).*')"
CLANG_TIDY_VERSION="clang-tidy $(clang-tidy --version  | grep -m 1 -Po '(?<=version ).*')"
CLANG_EXTDEF_MAPPINIG_VERSION="clang-extdef-mapping $(clang-extdef-mapping --version  | grep -m 1 -Po '(?<=version ).*')"
echo "Tools: $PYTHON_VERSION, $BAZEL_VERSION, $CODECHECKER_VERSION, $CLANG_VERSION, $CLANG_TIDY_VERSION, $CLANG_EXTDEF_MAPPINIG_VERSION"

if [[ -n "$VERBOSE_FLAG" ]]; then
    which python3
    which bazel
    which CodeChecker
    which clang
    which clang-tidy
    which clang-extdef-mapping
    which diagtool
fi
