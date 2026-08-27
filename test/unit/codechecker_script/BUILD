# Copyright 2026 Ericsson AB
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
    "@rules_cc//cc:defs.bzl",
    "cc_library",
)
load(
    "//:defs.bzl",
    "codechecker_test",
)
load(
    "//test/unit:unit_test.bzl",
    "unit_test",
)
load(
    "//test/unit/codechecker_script:action_test.bzl",
    "ANALYZE_OPTIONS",
    "action_test_suite",
)

# Defect free library: the tests check how the analysis is invoked
cc_library(
    name = "clean_lib",
    srcs = ["clean.cc"],
    tags = ["manual"],
)

# Real analyses, they also serve as subjects of the analysis tests below
codechecker_test(
    name = "monolithic_test",
    size = "small",
    analyze = ANALYZE_OPTIONS,
    targets = [":clean_lib"],
)

codechecker_test(
    name = "per_file_test",
    size = "small",
    analyze = ANALYZE_OPTIONS,
    per_file = True,
    targets = [":clean_lib"],
)

action_test_suite(
    name = "action",
    monolithic = ":monolithic_test",
    per_file = ":per_file_test",
)

# The analyzer paths of the toolchain reach CodeChecker via CC_ANALYZER_BIN
unit_test(
    name = "analyzers_test",
    contains = [
        "'CC_ANALYZER_BIN': 'clangsa:/",
        ";clang-tidy:/",
    ],
    data = [":monolithic_test"],
    files = "test/unit/codechecker_script/monolithic_test/codechecker.log",
)

# The parse step exports the results as json
unit_test(
    name = "parse_json_test",
    contains = [
        "version",
        "reports",
    ],
    data = [":monolithic_test"],
    files = "test/unit/codechecker_script/monolithic_test/codechecker-files/result.json",
)

# The parse step exports the results as html report
unit_test(
    name = "parse_html_test",
    contains = ["CodeChecker"],
    data = [":monolithic_test"],
    files = "test/unit/codechecker_script/monolithic_test/codechecker-files/report/index.html",
)
