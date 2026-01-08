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

load(
    "@bazel_codechecker//src:compile_commands.bzl",
    "compile_commands",
)

load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker_test",
)

# This is the important bit -- not only do we have an external dependency here
# in the form of external_lib, but is also an implementation_dep. This is a
# tricky edge case we need to handle.
cc_library(
    name = "intermediate_lib",
    srcs = ["intermediate.cpp"],
    hdrs = ["intermediate.h"],
    implementation_deps = ["@external_lib//:lib"],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "isystem_impl_dep",
    srcs = ["main.cc"],
    deps = [":intermediate_lib"],
)

compile_commands(
    name = "compile_commands_isystem",
    targets = [
        ":isystem_impl_dep",
    ],
)

codechecker_test(
    name = "codechecker_external_deps",
    targets = ["isystem_impl_dep"],
    tags = ["manual"],
)

codechecker_test(
    name = "per_file_external_deps",
    targets = ["isystem_impl_dep"],
    tags = ["manual"],
    per_file = True,
)
