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

# codechecker rules
load(
    "//src:codechecker.bzl",
    "codechecker",
    "codechecker_config",
    "codechecker_test",
)

# cc_binary for simple C++ tests
load(
    "@rules_cc//cc:defs.bzl",
    "cc_binary",
)

# C++ binary containing a division by zero bug
cc_binary(
    name = "test_zero",
    srcs = ["zero_div.cc"],
)

# The config files should disable check for the bug found in `zero_div.cc`
filegroup(
    name = "json_config_file",
    srcs = [":config.json"],
)

codechecker_config(
    name = "config_json",
    config_file = "json_config_file",
)

filegroup(
    name = "yaml_config_file",
    srcs = [":config.yaml"],
)

codechecker_config(
    name = "config_yaml",
    config_file = "yaml_config_file",
)

# None of these codechecker rules should find any issues
codechecker(
    name = "codechecker_json",
    config = "config_json",
    targets = [
        "test_zero",
    ],
)

codechecker(
    name = "codechecker_yaml",
    config = "config_yaml",
    targets = [
        "test_zero",
    ],
)

codechecker_test(
    name = "codechecker_test_json",
    config = "config_json",
    tags = ["manual"],
    targets = [
        "test_zero",
    ],
)

codechecker_test(
    name = "codechecker_test_yaml",
    config = "config_yaml",
    tags = ["manual"],
    targets = [
        "test_zero",
    ],
)

codechecker_test(
    name = "per_file_test_json",
    config = "config_json",
    per_file = True,
    tags = ["manual"],
    targets = [
        "test_zero",
    ],
)

codechecker_test(
    name = "per_file_test_yaml",
    config = "config_yaml",
    per_file = True,
    tags = ["manual"],
    targets = [
        "test_zero",
    ],
)
