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

git clone --recurse https://github.com/madler/zlib.git $1
git -C $1 checkout 5a82f71ed1dfc0bec044d9702463dbdf84ea3b71

# This file must be in the root of the project to be analyzed for bazelisk to work
bazelversion="../../../.bazelversion"
[ -f $bazelversion ] && cp $bazelversion $1

# Add codechecker to the project
cat <<EOF >> $1/BUILD.bazel
#-------------------------------------------------------

# codechecker rules
load(
    "@codechecker_bazel//src:codechecker.bzl",
    "codechecker_test",
)
codechecker_test(
    name = "codechecker_test",
    targets = [
        ":z",
    ],
)

codechecker_test(
    name = "per_file_test",
    targets = [
        ":z",
    ],
    per_file = True,
)

#-------------------------------------------------------
EOF

# Enable MODULE.bazel (in Bazel 6)
echo "common --enable_bzlmod" > $1/.bazelrc
# Add codechecker_bazel repo MODULE.bazel
cat ../templates/MODULE.template >> $1/MODULE.bazel
# An empty workspace file is required to keep Bazel versions older than 6.5.0
# in the project directory
touch $1/WORKSPACE
