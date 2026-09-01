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
Codechecker wrapper script for per-file analysis
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
# pylint outside bazel cannot follow the dependency graph
# This should be removed when pylint is integrated into bazel
from common import (  # pylint: disable=no-name-in-module
    check_results, fail, parse, setup_logging,
)


@dataclass
class Config:  # pylint: disable=too-many-instance-attributes
    """Configuration parsed from command-line arguments."""

    execution_mode: str
    verbosity: str
    severities: str
    codechecker_bin: str
    compile_commands: str
    codechecker_args: str
    config_file: str
    data_dir: str
    file_path: str
    log_file: str
    skip_file: str
    metadata_file: str
    analyzer_plist_paths: list
    analyzer_executables_env_var: str


def parse_args(argv=None):
    """Parse command-line arguments and return a Config instance."""
    parser = argparse.ArgumentParser(
        description="CodeChecker per-file analysis wrapper"
    )

    parser.add_argument("--mode", required=True, help="Execution mode")
    parser.add_argument("--verbosity", default="INFO", help="Log level")
    parser.add_argument(
        "--codechecker", required=False, help="Path to CodeChecker binary"
    )
    parser.add_argument(
        "--commands", required=False, help="Path to compile_commands.json"
    )
    parser.add_argument(
        "--analyze", default="", help="CodeChecker analyze arguments"
    )
    parser.add_argument("--config", required=False, help="Path to config file")
    parser.add_argument(
        "--data_dir", required=True, help="Output directory for CodeChecker"
    )
    parser.add_argument(
        "--file", required=False, help="Path to the file to be analyzed"
    )
    parser.add_argument(
        "--severities", required=False, help="Severities to check"
    )
    parser.add_argument("--log", required=False, help="Path to the log file")
    parser.add_argument("--skip", required=False, help="Path to the skip file")
    parser.add_argument(
        "--metadata", required=False, help="Path to the metadata file"
    )
    parser.add_argument(
        "--analyzer_plists",
        required=False,
        help="Semicolon-separated list of analyzer,plist_path pairs",
    )
    parser.add_argument(
        "--analyzer_executables",
        default="",
        help="Semicolon-separated list of name:path pairs",
    )

    args = parser.parse_args(argv)

    analyzer_plist_paths = []
    if args.analyzer_plists:
        analyzer_plist_paths = [
            item.split(",") for item in args.analyzer_plists.split(";")
        ]
    analyzer_executables_env_var = ""
    if args.analyzer_executables:
        analyzer_executables_env_var = ";".join(
            f"{name}:{os.path.realpath(path)}"
            for name, path in [
                pair.split(":", 1)
                for pair in args.analyzer_executables.split(";")
                if pair
            ]
        )

    return Config(
        execution_mode=args.mode,
        verbosity=args.verbosity,
        severities=args.severities,
        codechecker_bin=os.path.realpath(args.codechecker or "/"),
        compile_commands=args.commands,
        codechecker_args=args.analyze,
        config_file=args.config,
        data_dir=args.data_dir,
        file_path=args.file,
        log_file=args.log,
        skip_file=args.skip,
        metadata_file=args.metadata,
        analyzer_plist_paths=analyzer_plist_paths,
        analyzer_executables_env_var=analyzer_executables_env_var,
    )


COMPILE_COMMANDS_ABSOLUTE_SUFFIX = ".abs"

EMPTY_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>metadata</key>
	<dict>
		<key>generated_by</key>
		<dict>
			<key>name</key>
			<string>CodeChecker</string>
		</dict>
	</dict>
</dict>
</plist>
"""


def log(cfg: Config, msg: str) -> None:
    """
    Append message to the log file
    """
    with open(cfg.log_file, "a", encoding="utf-8") as log_file:
        log_file.write(msg)


def _compile_commands_absolute_path(cfg: Config) -> str:
    """Return the path for the absolute-paths version of
    compile_commands.json."""
    return cfg.compile_commands + COMPILE_COMMANDS_ABSOLUTE_SUFFIX


def _create_compile_commands_json_with_absolute_paths(cfg: Config):
    """
    Modifies the paths in compile_commands.json to contain the absolute path
    of the files.
    """
    absolute_path = _compile_commands_absolute_path(cfg)
    with open(
        cfg.compile_commands, "r", encoding="utf-8"
    ) as original_file, open(absolute_path, "w", encoding="utf-8") as new_file:
        content = original_file.read()
        # Replace "directory":"." with the absolute path
        # of the current working directory
        new_content = content.replace(
            '"directory":".', f'"directory":"{os.getcwd()}'
        )
        new_file.write(new_content)


def _get_codechecker_env(cfg: Config) -> dict[str, str]:
    """
    Returns the environment for running CodeChecker
    """
    cc_env = os.environ.copy()
    # Note: This is a workaround, CodeChecker requires the PATH to be set
    if "PATH" not in cc_env:
        cc_env["PATH"] = "/bin"
    # Overwrite analyzer paths
    cc_env["CC_ANALYZER_BIN"] = cfg.analyzer_executables_env_var
    return cc_env


def _run_codechecker(cfg: Config) -> None:
    """
    Runs CodeChecker analyze
    """
    absolute_path = _compile_commands_absolute_path(cfg)
    codechecker_cmd: list[str] = (
        [cfg.codechecker_bin, "analyze"]
        + cfg.codechecker_args.split()
        + ["--output=" + cfg.data_dir]
        + ["--file=*/" + cfg.file_path]
        + ["--skip", cfg.skip_file]
        + ["--config", cfg.config_file]
        + [absolute_path]
    )
    log(cfg, f"CodeChecker command: {' '.join(codechecker_cmd)}\n")
    log(cfg, "===---------------------------------------------===\n")
    log(cfg, "               CodeChecker error log               \n")
    log(cfg, "===---------------------------------------------===\n")

    result = subprocess.run(
        ["echo", "$PATH"],
        shell=True,
        env=_get_codechecker_env(cfg),
        capture_output=True,
        text=True,
        check=False,
    )
    log(cfg, result.stdout)

    try:
        with open(cfg.log_file, "a", encoding="utf-8") as log_file:
            subprocess.run(
                codechecker_cmd,
                env=_get_codechecker_env(cfg),
                stdout=log_file,
                stderr=log_file,
                check=True,
            )
    except subprocess.CalledProcessError as e:
        log(cfg, e.output.decode() if e.output else "")
        if e.returncode == 1 or e.returncode >= 128:
            _display_error(cfg, e.returncode)


def _display_error(cfg: Config, ret_code: int) -> None:
    """
    Display the log file, and exit with 1
    """
    # Log and exit on error
    print("===-----------------------------------------------------===")
    print(f"[ERROR]: CodeChecker returned with {ret_code}!")
    with open(cfg.log_file, "r", encoding="utf-8") as log_file:
        print(log_file.read())
    sys.exit(1)


def _move_output_files(cfg: Config):
    """
    Move output files from the temporary directory to their final destination
    If a file doesn't exists, write an empty output file to the target.
    This can happen when an analysis was skipped due to a CodeChecker skipfile.
    For each analysis action we must have an output file, even if its skipped,
    so we substitute it with an empty one.
    """
    # NOTE: the following we do to get rid of md5 hash in plist file names
    # Copy the plist files to the specified destinations
    destination_and_source_pattern_pairs = [
        (analyzer[1], re.compile(rf"_{analyzer[0]}_.*\.plist$"))
        for analyzer in cfg.analyzer_plist_paths
    ]

    plist_exists: bool = False

    for (
        destination_plist_path,
        source_plist_search_pattern,
    ) in destination_and_source_pattern_pairs:
        for file_path in os.listdir(cfg.data_dir):
            if not os.path.isfile(os.path.join(cfg.data_dir, file_path)):
                continue
            if source_plist_search_pattern.search(file_path):
                shutil.move(
                    os.path.join(cfg.data_dir, file_path),
                    destination_plist_path,
                )
                plist_exists = True
                break
        else:
            with open(destination_plist_path, "w", encoding="utf-8") as file:
                file.write(EMPTY_PLIST)

    # A CodeChecker-compliant result directory for the entire analysis may
    # have any number of plist files, but exactly one metadata.json file,
    # as described in
    # https://github.com/Ericsson/codechecker/blob/master/docs/report_directory.md.
    # The problem is that in per-file mode, each translation unit is analyzed
    # as a standalone analysis, each will have its own result directory and
    # metadata.json file. To remain complaint, we will eventually merge all
    # metadata files into a single one, but for now, we create a unique
    # metadata file name before copying it over.

    if os.path.isfile(os.path.join(cfg.data_dir, "metadata.json")):
        shutil.move(
            os.path.join(cfg.data_dir, "metadata.json"),
            cfg.metadata_file,
        )
    elif plist_exists:
        raise RuntimeError(
            "[ERROR] metadata.json doesn't exist despite "
            "successful analysis."
        )
    # This happens when the file was skipped.
    # CodeChecker does not create metadata
    # if no analysis was performed.
    else:
        with open(cfg.metadata_file, "w", encoding="utf-8") as file:
            file.write("{}")


def main():
    """
    Main function of CodeChecker wrapper
    """
    cfg = parse_args()
    setup_logging(cfg.verbosity, cfg.log_file)
    if cfg.execution_mode == "Run":
        _create_compile_commands_json_with_absolute_paths(cfg)
        _run_codechecker(cfg)
        _move_output_files(cfg)
    elif cfg.execution_mode == "Parse":
        with open(cfg.log_file, "a", encoding="utf-8"):
            pass
        parse(
            cfg.codechecker_bin,
            cfg.config_file,
            cfg.data_dir + "/../data",
            cfg.data_dir,
            cfg.log_file,
        )
    elif cfg.execution_mode == "Test":
        check_results(cfg.data_dir, cfg.log_file, cfg.severities)
    else:
        fail(
            cfg.log_file,
            f"Wrong codechecker script mode: {cfg.execution_mode}",
        )


if __name__ == "__main__":
    main()


# I have conserved this comment from the original bash script
# The sed commands are commented out, so we won't implement them
# sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" \
# $CLANG_TIDY_PLIST
# sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" $CLANGSA_PLIST
