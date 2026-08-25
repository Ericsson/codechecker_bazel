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

import os
import re
import shutil
import subprocess
import sys

COMPILE_COMMANDS_JSON: str = sys.argv[2]
COMPILE_COMMANDS_ABSOLUTE: str = f"{COMPILE_COMMANDS_JSON}.abs"
CODECHECKER_ARGS: str = sys.argv[3]
CONFIG_FILE: str = sys.argv[4]
SKIP_FILE: str = sys.argv[8]
CODECHECKER_BIN = os.path.realpath(sys.argv[1])
# The output directory for CodeChecker
DATA_DIR = sys.argv[5]
# The file to be analyzed
FILE_PATH = sys.argv[6]
LOG_FILE = sys.argv[7]
METADATA_FILE = sys.argv[9]
# List of pairs of analyzers and their plist files
ANALYZER_PLIST_PATHS = [item.split(",") for item in sys.argv[10].split(";")]
ANALYZER_EXECUTABLES_ENV_VAR = ";".join(
    f"{name}:{os.path.realpath(path)}"
    for name, path in [
        pair.split(":", 1) for pair in sys.argv[11].split(";") if pair
    ]
)


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


def log(msg: str) -> None:
    """
    Append message to the log file
    """
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(msg)


def _create_compile_commands_json_with_absolute_paths():
    """
    Modifies the paths in compile_commands.json to contain the absolute path
    of the files.
    """
    with open(
        COMPILE_COMMANDS_JSON, "r", encoding="utf-8"
    ) as original_file, open(
        COMPILE_COMMANDS_ABSOLUTE, "w", encoding="utf-8"
    ) as new_file:
        content = original_file.read()
        # Replace "directory":"." with the absolute path
        # of the current working directory
        new_content = content.replace(
            '"directory":".', f'"directory":"{os.getcwd()}'
        )
        new_file.write(new_content)


def _get_codechecker_env() -> dict[str, str]:
    """
    Returns the environment for running CodeChecker
    """
    cc_env = os.environ.copy()
    # Note: This is a workaround, CodeChecker requires the PATH to be set
    if "PATH" not in cc_env:
        cc_env["PATH"] = "/bin"
    # Overwrite analyzer paths
    cc_env["CC_ANALYZER_BIN"] = ANALYZER_EXECUTABLES_ENV_VAR
    return cc_env


def _run_codechecker() -> None:
    """
    Runs CodeChecker analyze
    """
    codechecker_cmd: list[str] = (
        [CODECHECKER_BIN, "analyze"]
        + CODECHECKER_ARGS.split()
        + ["--output=" + DATA_DIR]
        + ["--file=*/" + FILE_PATH]
        + ["--skip", SKIP_FILE]
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
        env=_get_codechecker_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    log(result.stdout)

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as log_file:
            subprocess.run(
                codechecker_cmd,
                env=_get_codechecker_env(),
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
    with open(LOG_FILE, "r", encoding="utf-8") as log_file:
        print(log_file.read())
    sys.exit(1)


def _move_output_files():
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
        for analyzer in ANALYZER_PLIST_PATHS
    ]

    plist_exists: bool = False

    for (
        destination_plist_path,
        source_plist_search_pattern,
    ) in destination_and_source_pattern_pairs:
        for file_path in os.listdir(DATA_DIR):
            if not os.path.isfile(os.path.join(DATA_DIR, file_path)):
                continue
            if source_plist_search_pattern.search(file_path):
                shutil.move(
                    os.path.join(DATA_DIR, file_path), destination_plist_path
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

    if os.path.isfile(os.path.join(DATA_DIR, "metadata.json")):
        shutil.move(os.path.join(DATA_DIR, "metadata.json"), METADATA_FILE)
    elif plist_exists:
        raise RuntimeError(
            "[ERROR] metadata.json doesn't exist despite successful analysis."
        )
    # This happens when the file was skipped.
    # CodeChecker does not create metadata
    # if no analysis was performed.
    else:
        with open(METADATA_FILE, "w", encoding="utf-8") as file:
            file.write("{}")


def main():
    """
    Main function of CodeChecker wrapper
    """
    if len(sys.argv) != 12:
        print("Wrong amount of arguments")
        sys.exit(1)
    _create_compile_commands_json_with_absolute_paths()
    _run_codechecker()
    _move_output_files()


if __name__ == "__main__":
    main()


# I have conserved this comment from the original bash script
# The sed commands are commented out, so we won't implement them
# sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" \
# $CLANG_TIDY_PLIST
# sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" $CLANGSA_PLIST
