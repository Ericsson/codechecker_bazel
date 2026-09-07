#!/usr/bin/env bash
# Copyright 2023 Ericsson AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

if [ ! -f /workspace/WORKSPACE ] && [ ! -f /workspace/WORKSPACE.bazel ]; then
    echo "[ERROR] /workspace does not look like a Bazel project root." >&2
    echo "        Mount your project: docker run --rm -v \"\$(pwd):/workspace\" ..." >&2
    exit 1
fi

# Copy every file into the sandbox to avoid permission errors
mkdir /tmp/rules_codechecker_test
# .git and files in .gitignore are not necessary for docker testing
rsync -a \
    --filter='+ /.bazelversion' \
    --exclude-from=/workspace/.gitignore \
    --exclude='.git' \
    /workspace/ /tmp/rules_codechecker_test/
cd /tmp/rules_codechecker_test

# Pass BAZEL_VERSION env var to pin a specific version at runtime, e.g.:
#   docker run --rm -e BAZEL_VERSION=7.7.0 -v "$(pwd):/workspace" ...
# defaults to 7.7.0
if [ -n "${BAZEL_VERSION:-}" ]; then
    echo "${BAZEL_VERSION}" > .bazelversion
    echo "[INFO] Pinned Bazel version to ${BAZEL_VERSION}"
elif [ ! -f ".bazelversion" ]; then
    echo "7.7.0" > .bazelversion
    echo "[INFO] No .bazelversion found, defaulting to 7.7.0"
fi

echo "========================================"
echo " Bazel version"
echo "========================================"
bazel version

echo "========================================"
echo " CodeChecker version"
echo "========================================"
CodeChecker version

echo "[NOTE]: CodeChecker may find different analyzer binaries" \
     "when invoking directly, or in bazel's sandbox environment!" \
     "Be sure to double check during debugging."

echo "========================================"
echo " Available analyzers"
echo "========================================"
CodeChecker analyzers

echo "========================================"
echo " Running tests"
echo "========================================"
echo "bazel test //..."
bazel test //...
echo "pylint ."
pylint .
echo "pytest test"
pytest test
