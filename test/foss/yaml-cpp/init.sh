#!/bin/bash

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
    "@codechecker_bazel//src:codechecker.bzl",
    "codechecker_test",
)


codechecker_test(
    name = "codechecker_test",
    targets = [
        ":yaml-cpp",
    ],
)

codechecker_test(
    name = "per_file_test",
    targets = [
        ":yaml-cpp",
    ],
    per_file = True,
)

#-------------------------------------------------------
EOF
# Apply bazel 8 specific flag, forcing the use of WORKSPACE
VERSION=$(< "../../templates/.bazelversion")
MAJOR_VERSION=${VERSION%%.*}
if [ "$MAJOR_VERSION" -eq 8 ]; then
    echo "common --enable_workspace" >> .bazelrc
fi
# Add codechecker_bazel repo to WORKSPACE
cat ../../templates/WORKSPACE.template >> WORKSPACE
