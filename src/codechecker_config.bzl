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

"""
Ruleset for configuring codechecker. 
"""

def _get_config_file_name(ctx):
    """
    Get the name of the config file.

    Returns the name of the config file to be used, with correct extension
    If no config file is given, we write the configuration options into a
    config.json file.
    Args:
        ctx: The context variable
    Returns:
        Path of the config file
    """
    if ctx.attr.config:
        if type(ctx.attr.config) == "list":
            config_info = ctx.attr.config[0][CodeCheckerConfigInfo]
        else:
            config_info = ctx.attr.config[CodeCheckerConfigInfo]
        if config_info.config_file:
            config_file = config_info.config_file.files.to_list()[0]
            config_file_name = ctx.attr.name + \
                               "/config." + config_file.extension
            return config_file_name
    config_file_name = ctx.attr.name + "/config.json"
    return config_file_name

def get_config_file(ctx):
    """
    Create config file for analysis

    Args:
        ctx: The context variable
    Returns:
        A tuple: (config_file, environment_variables)
        config_file is the file object to be read by Codechecker
    """

    # Declare config file to use during analysis
    config_file_name = _get_config_file_name(ctx)
    ctx_config_file = ctx.actions.declare_file(config_file_name)

    # Create CodeChecker JSON config file and env vars
    if ctx.attr.config:
        if type(ctx.attr.config) == "list":
            config_info = ctx.attr.config[0][CodeCheckerConfigInfo]
        else:
            config_info = ctx.attr.config[CodeCheckerConfigInfo]
        if config_info.config_file:
            # Symlink CodeChecker configuration file
            # provided via codechecker_config(config_file)
            config_file = config_info.config_file.files.to_list()[0]
            ctx.actions.symlink(
                output = ctx_config_file,
                target_file = config_file,
                progress_message = "Symlinking CodeChecker config file",
            )
        else:
            # Create CodeChecker configuration file in JSON format
            # from Bazel codechecker_config(analyze, parse)
            config_json = {}
            if config_info.analyze:
                config_json["analyze"] = config_info.analyze
            if config_info.parse:
                config_json["parse"] = config_info.parse
            config_content = json.encode_indent(config_json)
            ctx.actions.write(
                output = ctx_config_file,
                content = config_content,
                is_executable = False,
            )

        # Env vars for CodeChecker, one entry per variable
        codechecker_env = config_info.env
    else:
        # Empty CodeChecker JSON config file
        ctx.actions.write(
            output = ctx_config_file,
            content = "{}",
            is_executable = False,
        )
        codechecker_env = []
    return (ctx_config_file, codechecker_env)

CodeCheckerConfigInfo = provider(
    doc = "Defines CodeChecker configuration",
    fields = {
        "analyze": "List of arguments for CodeChecker analyze command",
        "config_file": "CodeChecker configuration file in JSON format",
        "env": "Environment variables for CodeChecker",
        "parse": "List of arguments for CodeChecker parse command",
    },
)

def _codechecker_config_impl(ctx):
    return [
        CodeCheckerConfigInfo(
            analyze = ctx.attr.analyze,
            parse = ctx.attr.parse,
            config_file = ctx.attr.config_file,
            env = ctx.attr.env,
        ),
    ]

codechecker_config_internal = rule(
    implementation = _codechecker_config_impl,
    attrs = {
        "analyze": attr.string_list(
            default = [],
            doc = "List of arguments for CodeChecker analyze command",
        ),
        "config_file": attr.label(
            default = None,
            allow_single_file = True,
        ),
        "env": attr.string_list(
            default = [],
            doc = "List of environment variables for CodeChecker",
        ),
        "parse": attr.string_list(
            default = [],
            doc = "List of arguments for CodeChecker parse command",
        ),
    },
)
