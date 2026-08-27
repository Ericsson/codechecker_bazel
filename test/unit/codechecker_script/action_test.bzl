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

"""
Analysis tests for how the CodeChecker action invokes its script py_binary.

NOTE: Both invariants below fail only under remote execution,
      therefore they are asserted at analysis time:

- The action must execute py_binary itself, not a per-target symlink to it.
  Symlink points into the local output base and breaks runfiles lookup.
  The stub looks for runfiles next to argv[0], and follows argv[0] when it is
  a symlink, into the local output base, where a remote worker has nothing.

- Arguments must not carry literal shell quoting.
  ctx.actions.args() builds argv directly, so quotes are ordinary characters.
  They become quoting when the script interpolates them into its shell command,
  collapsing the analyze options into one argument.
"""

load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts")

# The following is used for quoting test.
# NOTE: two or more options are needed, a single option survives the quoting
ANALYZE_OPTIONS = [
    "--ctu",
    "--disable=cplusplus",
]

def _codechecker_actions(env):
    """Return the actions with the CodeChecker mnemonic"""
    return [
        action
        for action in analysistest.target_actions(env)
        if action.mnemonic == "CodeChecker"
    ]

def _assert_executes_script_directly(env, action, script_name):
    """Assert argv[0] is the shared py_binary, not a per-target symlink.

    Args:
        env: Analysis test environment.
        action: Action to inspect.
        script_name: Basename of the expected script executable.
    """
    label = analysistest.target_under_test(env).label
    argv0 = action.argv[0]

    asserts.true(
        env,
        argv0.endswith(script_name),
        "Expected argv[0] to be the {} executable, got: {}".format(
            script_name,
            argv0,
        ),
    )

    # A per-target symlink is declared in the target's own output directory,
    # so its path contains the target name. The py_binary lives under src/.
    asserts.false(
        env,
        "/{}/{}".format(label.name, script_name) in argv0,
        "Per-target symlink instead of the {} py_binary: {}".format(
            script_name,
            argv0,
        ),
    )

def _assert_no_shell_quoting(env, action):
    """Assert that no argument carries literal quote characters.

    Args:
        env: Analysis test environment.
        action: Action to inspect.
    """
    for arg in action.argv:
        asserts.false(
            env,
            "'" in arg,
            "Argument carries a literal quote: {}".format(arg),
        )

def _monolithic_action_test_impl(ctx):
    env = analysistest.begin(ctx)

    actions = _codechecker_actions(env)
    asserts.equals(
        env,
        1,
        len(actions),
        "Expected exactly one CodeChecker action, got {}".format(len(actions)),
    )

    if len(actions) == 1:
        action = actions[0]
        _assert_executes_script_directly(env, action, "codechecker_script")
        _assert_no_shell_quoting(env, action)

        # The options should reach script as a single --analyze=<opts> token:
        # argparse rejects a separate value that starts with a dash.
        expected = "--analyze=" + " ".join(ANALYZE_OPTIONS)
        asserts.true(
            env,
            expected in action.argv,
            "Expected {} in argv, got: {}".format(expected, action.argv),
        )

    return analysistest.end(env)

monolithic_action_test = analysistest.make(_monolithic_action_test_impl)

def _per_file_action_test_impl(ctx):
    env = analysistest.begin(ctx)

    actions = _codechecker_actions(env)
    asserts.true(
        env,
        len(actions) > 0,
        "Expected at least one CodeChecker action",
    )

    for action in actions:
        _assert_executes_script_directly(env, action, "per_file_script")
        _assert_no_shell_quoting(env, action)

    return analysistest.end(env)

per_file_action_test = analysistest.make(_per_file_action_test_impl)

def action_test_suite(name, monolithic, per_file):
    """Instantiate the analysis tests for both rule flavours.

    Args:
        name: Name prefix of the generated targets.
        monolithic: Target using the monolithic rule.
        per_file: Target using per_file = True.
    """
    monolithic_action_test(
        name = name + "_monolithic_test",
        size = "small",
        target_under_test = monolithic,
    )

    per_file_action_test(
        name = name + "_per_file_test",
        size = "small",
        target_under_test = per_file,
    )

    native.test_suite(
        name = name,
        tests = [
            name + "_monolithic_test",
            name + "_per_file_test",
        ],
    )
