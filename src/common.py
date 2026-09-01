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
Common utilities for CodeChecker rules
"""

import logging
import re
import shlex
import subprocess
import sys
import os


def read_file(codechecker_log, filename):
    """Read text file and return its contents"""
    if not os.path.isfile(filename):
        fail(codechecker_log, f"File not found: {filename}")
    with open(filename, encoding="utf-8") as handle:
        return handle.read()


def separator(method="info"):
    """Print log separator line to logging.info() or other logging methods"""
    getattr(logging, method)("#" * 23)


def stage(title, method="info"):
    """Print stage title into log"""
    separator(method)
    getattr(logging, method)("### " + title)
    separator(method)


def valid_parameter(parameter):
    """Check if external parameter is defined and valid"""
    if parameter is None:
        return False
    if parameter and parameter[0] == "{":
        return False
    return True


def log_file_name(codechecker_log):
    """Check and return log file name"""
    if valid_parameter(codechecker_log):
        return codechecker_log
    return None


def fail(codechecker_log, message, exit_code=1):
    """Print error message and return exit code"""
    logging.error(message)
    print()
    print("*" * 50)
    print("codechecker script execution FAILED!")
    if log_file_name(codechecker_log):
        print(f"See: {log_file_name(codechecker_log)}")
        print("*" * 50)
        try:
            with open(
                log_file_name(codechecker_log), encoding="utf-8"
            ) as log_file:
                print(log_file.read())
        except IOError:
            print("File not accessible")
    else:
        print(message)
    print("*" * 50)
    print()
    sys.exit(exit_code)


def execute(codechecker_log, cmd, env=None, codes=None):
    """Execute CodeChecker commands"""
    if codes is None:
        codes = [0]
    with subprocess.Popen(
        cmd,
        env=env,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        stdout, stderr = process.communicate()
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")
        if process.returncode not in codes:
            fail(
                codechecker_log,
                f"\ncommand: {cmd}\nstdout: {stdout}\nstderr: {stderr}\n",
            )
        logging.debug("Executing: %s", cmd)
        # logging.debug("Output:\n\n%s\n", stdout)
    return stdout


def parse(codechecker_path, config, plist_folder, output_folder, log):
    """Run CodeChecker parse commands"""
    stage("CodeChecker parse:")
    logging.info("CodeChecker parse -e json")
    codechecker_parse = (
        f"{codechecker_path} parse --config "
        f"{config} {plist_folder}"
    )
    # Save results to JSON file
    command = (
        f"{codechecker_parse} --export=json > "
        f"{output_folder}/result.json"
    )
    execute(log, command, codes=[0, 2])
    # Save results as HTML report
    logging.info("CodeChecker parse -e html")
    command = (
        codechecker_parse
        + " --export=html --output="
        + output_folder
        + "/report"
    )
    execute(log, command, codes=[0, 2])
    # Save results to text file
    logging.info("CodeChecker parse to text result")
    command = codechecker_parse + " > " + output_folder + "/result.txt"
    execute(log, command, codes=[0, 2])
    logging.info(
        "Result:\n\n%s\n",
        read_file(log, output_folder + "/result.txt"),
    )


def check_results(data_dir, log, severities):
    """Check/verify CodeChecker results"""
    stage("Checking result:")
    # Get results file and read it
    result_file = data_dir + "/result.txt"
    logging.info("Find CodeChecker results in bazel-out")
    logging.info("      all artifacts: %s/", data_dir)
    logging.info(
        "      HTML report:   %s/report/index.html", data_dir
    )
    logging.info("      result file:   %s", result_file)
    results = read_file(log, result_file)
    logging.info("Results: \n\n%s\n", results)
    # Collect defect severities to detect
    if not valid_parameter(severities):
        fail(
            log,
            "CodeChecker defect severities are invalid: "
            f"{str(severities)}",
        )
    severities = shlex.split(severities)
    # Add HIGH severity by default
    if not severities:
        severities.append("HIGH")
    # We should always detect CRITICAL defects
    if "CRITICAL" not in severities:
        severities.append("CRITICAL")
    logging.debug("Severities: %s", str(severities))
    issues = dict.fromkeys(severities, 0)
    logging.debug("Issues: %s", str(issues))
    # Grep results for defects according to severities
    for issue in issues:
        found = re.findall(rf"^{issue} .* (\d+)", results, re.M)
        defects = sum(int(number) for number in found)
        logging.debug("   %s : %s = %d", issue, str(found), defects)
        issues[issue] = defects
    logging.info("Defects: %s", str(issues))
    # Check collected defects
    passed = True
    conclusion = ""
    for issue, num in issues.items():
        if num > 0:
            passed = False
            conclusion += f"{issue:>15} : {num}\n"
    if passed:
        logging.info("No defects found by CodeChecker")
    else:
        fail(log, f"CodeChecker found defects:\n{conclusion}")


def setup_logging(verbosity, log):
    """Setup logging parameters for execution session"""
    if verbosity == "INFO":
        log_level = logging.INFO
    elif verbosity == "WARN":
        log_level = logging.WARN
    else:
        log_level = logging.DEBUG
    log_format = "[codechecker] %(levelname)5s: %(message)s"

    if log_file_name(log):
        logging.basicConfig(
            filename=log_file_name(log),
            level=log_level,
            format=log_format,
        )
    else:
        logging.basicConfig(level=log_level, format=log_format)
