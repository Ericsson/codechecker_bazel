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

"""Minimal skylib unit test example.

Tests pure Starlark functions without needing real Bazel targets.
"""

load("@bazel_skylib//lib:unittest.bzl", "asserts", "unittest")
load("//src:per_file.bzl", "check_valid_file_type")

# ---------------------------------------------------------------------------
# Helpers — fake struct to stand in for a File object
# ---------------------------------------------------------------------------

def _fake_file(basename):
    return struct(basename = basename)

# ---------------------------------------------------------------------------
# Test: check_valid_file_type accepts C/C++ files
# ---------------------------------------------------------------------------

def _valid_file_types_test_impl(ctx):
    env = unittest.begin(ctx)

    asserts.true(env, check_valid_file_type(_fake_file("main.c")))
    asserts.true(env, check_valid_file_type(_fake_file("main.cc")))
    asserts.true(env, check_valid_file_type(_fake_file("main.cpp")))
    asserts.true(env, check_valid_file_type(_fake_file("main.cxx")))

    return unittest.end(env)

valid_file_types_test = unittest.make(_valid_file_types_test_impl)

# ---------------------------------------------------------------------------
# Test: check_valid_file_type rejects non-C/C++ files
# ---------------------------------------------------------------------------

def _invalid_file_types_test_impl(ctx):
    env = unittest.begin(ctx)

    asserts.false(env, check_valid_file_type(_fake_file("script.py")))
    asserts.false(env, check_valid_file_type(_fake_file("data.json")))
    asserts.false(env, check_valid_file_type(_fake_file("header.h")))
    asserts.false(env, check_valid_file_type(_fake_file("header.hpp")))
    asserts.false(env, check_valid_file_type(_fake_file("BUILD")))
    asserts.false(env, check_valid_file_type(_fake_file("rules.bzl")))

    return unittest.end(env)

invalid_file_types_test = unittest.make(_invalid_file_types_test_impl)

# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

def unit_test_suite(name):
    """Instantiates the basic skylib unit tests.

    Args:
        name: Name prefix for the generated test targets.
    """
    valid_file_types_test(name = name + "_valid_file_types")
    invalid_file_types_test(name = name + "_invalid_file_types")

    native.test_suite(
        name = name,
        tests = [
            ":" + name + "_valid_file_types",
            ":" + name + "_invalid_file_types",
        ],
    )
