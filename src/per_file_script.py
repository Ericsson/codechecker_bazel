#!{PythonPath}

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


import os
import re
import shutil
import subprocess
import sys
from typing import Optional

# The output directory for CodeChecker
DATA_DIR: Optional[str] = None
# The file to be analyzed
FILE_PATH: Optional[str] = None
# List of pairs of analyzers and their plist files
ANALYZER_PLIST_PATHS: Optional[list[list[str]]] = None
LOG_FILE: Optional[str] = None
COMPILE_COMMANDS_JSON: str = "{compile_commands_json}"
COMPILE_COMMANDS_ABSOLUTE: str = f"{COMPILE_COMMANDS_JSON}.abs"
CODECHECKER_ARGS: str = "{codechecker_args}"
CONFIG_FILE: str = "{config_file}"


def parse_args():
    """
    Parse arguments that may change from file-to-file.
    """
    if len(sys.argv) != 5:
        print("Wrong amount of arguments")
        sys.exit(1)

    global DATA_DIR
    global FILE_PATH
    global LOG_FILE
    global ANALYZER_PLIST_PATHS

    DATA_DIR = sys.argv[1]
    FILE_PATH = sys.argv[2]
    LOG_FILE = sys.argv[3]
    ANALYZER_PLIST_PATHS = [item.split(",") for item in sys.argv[4].split(";")]


def log(msg: str) -> None:
    """
    Append message to the log file
    """
    with open(LOG_FILE, "a") as log_file:  # type: ignore
        log_file.write(msg)


def _create_compile_commands_json_with_absolute_paths():
    """
    Modifies the paths in compile_commands.json to contain the absolute path
    of the files.
    """
    with open(COMPILE_COMMANDS_JSON, "r") as original_file, open(
        COMPILE_COMMANDS_ABSOLUTE, "w"
    ) as new_file:
        content = original_file.read()
        # Replace "directory":"." with the absolute path
        # of the current working directory
        new_content = content.replace(
            '"directory":".', f'"directory":"{os.getcwd()}'
        )
        new_file.write(new_content)


def _run_codechecker() -> None:
    """
    Runs CodeChecker analyze
    """
    codechecker_cmd: list[str] = (
        ["CodeChecker", "analyze"]
        + CODECHECKER_ARGS.split()
        + ["--output=" + DATA_DIR]  # type: ignore
        + ["--file=*/" + FILE_PATH]  # type: ignore
        + ["--config", CONFIG_FILE]
        + [COMPILE_COMMANDS_ABSOLUTE]
    )
    log(f"CodeChecker command: {' '.join(codechecker_cmd)}\n")
    log("===-----------------------------------------------------===\n")
    log("                   CodeChecker error log                   \n")
    log("===-----------------------------------------------------===\n")

    result = subprocess.run(
        ["echo", "$PATH"],
        shell=True,
        env=os.environ,
        capture_output=True,
        text=True,
    )
    log(result.stdout)


    try:
        with open(LOG_FILE, "a") as log_file:  # type: ignore
            subprocess.run(
                codechecker_cmd,
                env=os.environ,
                stdout=log_file,
                stderr=log_file,
                check=True,
            )
    except subprocess.CalledProcessError as e:
        log(e.output.decode() if e.output else "")
        if e.returncode == 1 or e.returncode >= 128:
            _display_error(e.returncode)


def _display_error(ret_code: int) -> None:
    """
    Display the log file, and exit with 1
    """
    # Log and exit on error
    print("===-----------------------------------------------------===")
    print(f"[ERROR]: CodeChecker returned with {ret_code}!")
    with open(LOG_FILE, "r") as log_file:  # type: ignore
        print(log_file.read())
    sys.exit(1)


def _move_plist_files():
    """
    Move the plist files from the temporary directory to their final destination
    """
    # NOTE: the following we do to get rid of md5 hash in plist file names
    # Copy the plist files to the specified destinations
    for file in os.listdir(DATA_DIR):
        for analyzer_info in ANALYZER_PLIST_PATHS:  # type: ignore
            if re.search(
                rf"_{analyzer_info[0]}_.*\.plist$", file
            ) and os.path.isfile(
                os.path.join(DATA_DIR, file)
            ):  # type: ignore
                shutil.move(os.path.join(DATA_DIR, file), analyzer_info[1])  # type: ignore


def main():
    parse_args()
    _create_compile_commands_json_with_absolute_paths()
    _run_codechecker()
    _move_plist_files()


if __name__ == "__main__":
    main()


# I have conserved this comment from the original bash script
# The sed commands are commented out, so we won't implement them
# # sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" $CLANG_TIDY_PLIST
# # sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" $CLANGSA_PLIST
