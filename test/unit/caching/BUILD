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
    "//test/unit/caching:caching_test.bzl",
    "caching_test",
)

# We are not interested in finding bugs, we are only interested in whether the
# analysis re-runs after the files have been modified. As such, these files emit no
# warnings.

exports_files(["caching_check.py"])

# Bazel-native caching tests (bazel inside bazel)
caching_test(
    name = "caching_monolithic_test",
    expected_action_count = 1,
    file_to_modify = "secondary.cc",
    target_name = "codechecker_caching",
)

caching_test(
    name = "caching_per_file_test",
    expected_action_count = 2,
    file_to_modify = "secondary.cc",
    target_name = "per_file_caching",
)

caching_test(
    name = "caching_per_file_ctu_test",
    expected_action_count = 3,
    file_to_modify = "secondary.cc",
    target_name = "per_file_caching_ctu",
)
