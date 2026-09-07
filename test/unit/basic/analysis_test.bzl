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

"""Minimal skylib analysis test example.

Verifies that compile_commands_aspect populates SourceFilesInfo with
the expected source file.
"""

load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts")
load(
    "//src:compile_commands.bzl",
    "SourceFilesInfo",
    "compile_commands_aspect",
)

# ---------------------------------------------------------------------------
# Test: compilation database is non-empty
# ---------------------------------------------------------------------------

def _compilation_db_nonempty_test_impl(ctx):
    env = analysistest.begin(ctx)

    target = analysistest.target_under_test(env)
    db = target[SourceFilesInfo].compilation_db.to_list()

    asserts.true(
        env,
        len(db) > 0,
        "compilation_db should contain at least one entry",
    )

    return analysistest.end(env)

compilation_db_nonempty_test = analysistest.make(
    _compilation_db_nonempty_test_impl,
    extra_target_under_test_aspects = [compile_commands_aspect],
)

# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

def analysis_test_suite(name):
    """Instantiates the basic skylib analysis tests.

    Args:
        name: Name prefix for the generated test targets.
    """

    compilation_db_nonempty_test(
        name = name + "_compilation_db_nonempty",
        target_under_test = ":basic_target",
    )

    native.test_suite(
        name = name,
        tests = [
            ":" + name + "_compilation_db_nonempty",
        ],
    )
