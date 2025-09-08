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

DATA_DIR: str = "{data_dir}"
ANALYZER_PLIST_PATHS: list[tuple[str, str]] = {analyzer_output_list}
LOG_FILE: str = "{log_file}"
COMPILE_COMMANDS_JSON: str = "{compile_commands_json}"
COMPILE_COMMANDS_ABSOLUTE: str = f"{COMPILE_COMMANDS_JSON}.abs"
CODECHECKER_ARGS: str = "{codechecker_args}"


def log(msg: str) -> None:
    with open(LOG_FILE, "a") as log_file:
        log_file.write(msg)


with open(COMPILE_COMMANDS_JSON, "r") as original_file, open(
    COMPILE_COMMANDS_ABSOLUTE, "w"
) as new_file:
    content = original_file.read()
    # Replace '"directory":"."' with the absolute path
    # of the current working directory
    new_content = content.replace(
        '"directory":".', f'"directory":"{os.getcwd()}'
    )
    new_file.write(new_content)

with open(LOG_FILE, "w") as log_file:
    log_file.write(
        f"CodeChecker command: CodeChecker analyze {CODECHECKER_ARGS} \
{COMPILE_COMMANDS_ABSOLUTE}\n"
    )
    log_file.write(
        "===-----------------------------------------------------===\n"
    )
    log_file.write(
        "                   CodeChecker error log                   \n"
    )
    log_file.write(
        "===-----------------------------------------------------===\n"
    )

result = subprocess.run(
    ["echo", "$PATH"],
    shell=True,
    env=os.environ,
    capture_output=True,
    text=True,
)
log(result.stdout)

codechecker_cmd: list[str] = (
    ["CodeChecker", "analyze"]
    + CODECHECKER_ARGS.split()
    + [COMPILE_COMMANDS_ABSOLUTE]
)

try:
    with open(LOG_FILE, "a") as log_file:
        proc = subprocess.run(
            codechecker_cmd,
            env=os.environ,
            stdout=log_file,
            stderr=log_file,
            check=True,
        )
    ret_code = 0
except subprocess.CalledProcessError as e:
    ret_code = e.returncode
    with open(LOG_FILE, "a") as log_file:
        log_file.write(e.output.decode() if e.output else "")

# Log and exit on error
if ret_code == 1 or ret_code >= 128:
    print("===-----------------------------------------------------===")
    print(f"[ERROR]: CodeChecker returned with {ret_code}!")
    with open(LOG_FILE, "r") as log_file:
        print(log_file.read())
    sys.exit(1)

# NOTE: the following we do to get rid of md5 hash in plist file names
# Copy the plist files to the specified destinations
for file in os.listdir(DATA_DIR):
    for analyzer_info in ANALYZER_PLIST_PATHS:
        if re.search(
            rf"_{analyzer_info[0]}_.*\.plist$", file
        ) and os.path.isfile(os.path.join(DATA_DIR, file)):
            shutil.copy(os.path.join(DATA_DIR, file), analyzer_info[1])

# I have conserved this comment from the original bash script
# The sed commands are commented out, so we won't implement them
# # sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" $CLANG_TIDY_PLIST
# # sed -i -e "s|<string>.*execroot/bazel_codechecker/|<string>|g" $CLANGSA_PLIST
