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

# cc_binary for simple C++ tests
load(
    "@rules_cc//cc:defs.bzl",
    "cc_binary",
)

# codechecker rules
load(
    "//:defs.bzl",
    "codechecker_config",
    "codechecker_test",
)

# build only codechecker rule, internal
load(
    "//src:codechecker.bzl",
    "codechecker",
)
load(
    "//test/unit:unit_test.bzl",
    "unit_test",
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

# The env entries of the config have to reach the CodeChecker environment
codechecker_config(
    name = "config_env",
    config_file = "json_config_file",
    env = [
        "CC_TEST_VAR=42",
        "CC_TEST_PATH=/tmp/first:/tmp/second",
        "CC_TEST_FLAGS=-DFIRST=1 -DSECOND=2",
        # Values may contain the "; " that used to separate the entries
        "CC_TEST_PAIRS=VAR1=1; VAR2=2",
        "CC_TEST_LIST=1; 2; 3;",
    ],
)

codechecker_test(
    name = "codechecker_env",
    config = "config_env",
    tags = ["manual"],
    targets = [
        "test_zero",
    ],
)

unit_test(
    name = "codechecker_env_test",
    contains = [
        "'CC_TEST_VAR': '42'",
        "'CC_TEST_PATH': '/tmp/first:/tmp/second'",
        "'CC_TEST_FLAGS': '-DFIRST=1 -DSECOND=2'",
        "'CC_TEST_PAIRS': 'VAR1=1; VAR2=2'",
        "'CC_TEST_LIST': '1; 2; 3;'",
    ],
    data = [":codechecker_env"],
    files = "test/unit/config/codechecker_env/codechecker.log",
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

unit_test(
    name = "codechecker_json_test",
    contains = r"disable=core.DivideZero\",",
    data = [":codechecker_json"],
    files = "test/unit/config/codechecker_json/config.json",
)

unit_test(
    name = "codechecker_yaml_test",
    contains = r"- \"--disable=core.DivideZero\"",
    data = [":codechecker_yaml"],
    files = "test/unit/config/codechecker_yaml/config.yaml",
)

unit_test(
    name = "codechecker_test_json_test",
    contains = r"disable=core.DivideZero\",",
    data = [":codechecker_test_json"],
    files = "test/unit/config/codechecker_test_json/config.json",
)

unit_test(
    name = "codechecker_test_yaml_test",
    contains = r"- \"--disable=core.DivideZero\"",
    data = [":codechecker_test_yaml"],
    files = "test/unit/config/codechecker_test_yaml/config.yaml",
)

unit_test(
    name = "per_file_test_json_test",
    contains = r"disable=core.DivideZero\",",
    data = [":per_file_test_json"],
    files = "test/unit/config/per_file_test_json/config.json",
)

unit_test(
    name = "per_file_test_yaml_test",
    contains = r"- \"--disable=core.DivideZero\"",
    data = [":per_file_test_yaml"],
    files = "test/unit/config/per_file_test_yaml/config.yaml",
)
