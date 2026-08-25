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
CodeChecker Bazel build & test wrapper script
"""

from __future__ import print_function
from dataclasses import dataclass
import logging
import os
import plistlib
import re
import shlex
import subprocess
import sys
import argparse


@dataclass
class Config:  # pylint: disable=too-many-instance-attributes
    """Configuration parsed from command-line arguments."""

    execution_mode: str
    verbosity: str
    codechecker_path: str
    compile_commands: str
    clang_path: str
    clang_tidy_path: str
    codechecker_skipfile: str
    codechecker_config: str
    codechecker_analyze: str
    codechecker_files: str
    codechecker_log: str
    codechecker_env: str
    codechecker_severities: str


START_PATH = r"\/(?:(?!\.\s+)\S)+"
BAZEL_PATHS = {
    r"\/sandbox\/processwrapper-sandbox\/\S*\/execroot\/": "/execroot/",
    START_PATH + r"\/worker\/build\/[0-9a-fA-F]{16}\/root\/": "",
    START_PATH + r"\/[0-9a-fA-F]{32}\/execroot\/": "",
}


def parse_args(argv=None):
    """Parse command-line arguments and return a Config instance."""
    parser = argparse.ArgumentParser(description="CodeChecker Bazel Wrapper")

    parser.add_argument("--mode", required=True, help="Execution mode")
    parser.add_argument("--verbosity", default="INFO", help="Log level")
    parser.add_argument(
        "--codechecker_path", required=True, help="CodeChecker path"
    )
    parser.add_argument("--clang_tidy", required=False, help="clang-tidy path")
    parser.add_argument("--clang", required=False, help="clang path")
    parser.add_argument("--commands", help="Compile commands json")
    parser.add_argument("--skip", help="Skipfile path")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument("--analyze", default="", help="Analysis options")
    parser.add_argument(
        "--files", help="Folder where CodeChecker will store its results"
    )
    parser.add_argument("--log", help="Log file path")
    parser.add_argument("--env", help="Environment for CodeChecker")
    parser.add_argument("--severities", help="List of severities to fail on")

    args = parser.parse_args(argv)

    return Config(
        execution_mode=args.mode,
        verbosity=args.verbosity,
        codechecker_path=os.path.realpath(args.codechecker_path),
        compile_commands=args.commands,
        clang_path=os.path.realpath(args.clang) if args.clang else None,
        clang_tidy_path=(
            os.path.realpath(args.clang_tidy) if args.clang_tidy else None
        ),
        codechecker_skipfile=args.skip,
        codechecker_config=args.config,
        codechecker_analyze=args.analyze,
        codechecker_files=args.files,
        codechecker_log=args.log,
        codechecker_env=args.env,
        codechecker_severities=args.severities,
    )


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


def setup(verbosity, codechecker_log):
    """Setup logging parameters for execution session"""
    if verbosity == "INFO":
        log_level = logging.INFO
    elif verbosity == "WARN":
        log_level = logging.WARN
    else:
        log_level = logging.DEBUG
    log_format = "[codechecker] %(levelname)5s: %(message)s"

    if log_file_name(codechecker_log):
        logging.basicConfig(
            filename=log_file_name(codechecker_log),
            level=log_level,
            format=log_format,
        )
    else:
        logging.basicConfig(level=log_level, format=log_format)


def input_data(cfg):
    """Print out input (external) parameters"""
    stage("CodeChecker input data:", "debug")
    logging.debug("EXECUTION_MODE       : %s", str(cfg.execution_mode))
    logging.debug("VERBOSITY            : %s", str(cfg.verbosity))
    logging.debug("CODECHECKER_PATH     : %s", str(cfg.codechecker_path))
    logging.debug("CODECHECKER_SKIPFILE : %s", str(cfg.codechecker_skipfile))
    logging.debug("CODECHECKER_CONFIG   : %s", str(cfg.codechecker_config))
    logging.debug("CODECHECKER_ANALYZE  : %s", str(cfg.codechecker_analyze))
    logging.debug("CODECHECKER_FILES    : %s", str(cfg.codechecker_files))
    logging.debug("CODECHECKER_LOG      : %s", str(cfg.codechecker_log))
    logging.debug("CODECHECKER_ENV      : %s", str(cfg.codechecker_env))
    logging.debug("COMPILE_COMMANDS     : %s", str(cfg.compile_commands))
    logging.debug("")


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


def create_folder(path):
    """Create folder structure for CodeChecker data files and reports"""
    if not os.path.exists(path):
        os.makedirs(path)


def prepare(codechecker_files):
    """Prepare CodeChecker execution environment"""
    stage("CodeChecker files:")
    logging.info("Creating folder: %s", codechecker_files)
    create_folder(codechecker_files)


def generate_analyzer_executables(cfg):
    """
    Generates the value for the CC_ANALYZER_BIN environment variable
    """
    analyzer_executables = (
        f"clangsa:{cfg.clang_path};clang-tidy:{cfg.clang_tidy_path}"
    )
    return analyzer_executables


def analyze(cfg):
    """Run CodeChecker analyze command"""
    stage("CodeChecker analyze:")

    env = os.environ
    if cfg.codechecker_env:
        env_list = cfg.codechecker_env.split("; ")
        if env_list:
            codechecker_env = dict(item.split("=", 1) for item in env_list)
            env.update(codechecker_env)
    # Note: This is a workaround, CodeChecker requires the PATH to be set
    if "PATH" not in env:
        env["PATH"] = "/bin"
    env["CC_ANALYZER_BIN"] = generate_analyzer_executables(cfg)
    logging.debug("env: %s", str(env))

    output = execute(
        cfg.codechecker_log,
        f"{cfg.codechecker_path} analyzers --details",
        env=env,
    )
    logging.debug("Analyzers:\n\n%s", output)

    command = (
        f"{cfg.codechecker_path} analyze --skip={cfg.codechecker_skipfile} "
        f"{cfg.compile_commands} --output={cfg.codechecker_files}/data "
        f"--config {cfg.codechecker_config} {cfg.codechecker_analyze}"
    )
    # FIXME: Workaround "CodeChecker simply remove compiler-rt include path".
    # This can be removed once codechecker 6.16.0 is used.
    # command += " --keep-gcc-intrin"
    logging.info("Running CodeChecker analyze...")
    output = execute(cfg.codechecker_log, command, env=env)
    logging.info("Output:\n\n%s\n", output)
    if output.find("- Failed to analyze") != -1:
        logging.error("CodeChecker failed to analyze some files")
        fail(
            cfg.codechecker_log, "Make sure that the target can be built first"
        )


def fix_path_with_regex(data: str) -> str:
    """
    The absolute paths of the analyzed source files found in the plist files
    do not point to their original location, but rather wherever bazel copied
    them. This might either be in a subdirectory in bazel-bin on the
    local machine, or somewhere unrelated if the analysis was executed on a
    remote worker. This function tries to replace these paths to the location
    of the original location of the source file.
    """
    for pattern, replace in BAZEL_PATHS.items():
        data = re.sub(pattern, replace, data)
    return data


def fix_bazel_paths(codechecker_files):
    """Remove Bazel leading paths in all files"""
    stage("Fix CodeChecker output:")
    folder = codechecker_files
    logging.info("Fixing Bazel paths in %s", folder)
    counter = 0
    for root, _, files in os.walk(folder):
        for filename in files:
            fullpath = os.path.join(root, filename)
            with open(fullpath, "rt", encoding="utf-8") as data_file:
                data = fix_path_with_regex(data_file.read())
            with open(fullpath, "w", encoding="utf-8") as data_file:
                data_file.write(data)
            counter += 1
    logging.info("Fixed Bazel paths in %d files", counter)


def realpath(filename):
    """Return real full absolute path for given filename"""
    if os.path.exists(filename):
        real_file_name = os.path.abspath(os.path.realpath(filename))
        logging.debug("Updating %s -> %s", filename, real_file_name)
        filename = real_file_name
    return filename


def resolve_plist_symlinks(filepath):
    """Resolve the symbolic links in plist files to real file paths"""
    # plistlib replaced readPlist/writePlist with load/dump in Python 3.9.
    # Since Pylint analyzes every line,
    # it flags the methods missing in the current environment.
    # pylint: disable=no-member
    logging.info("Processing plist file: %s", filepath)
    if sys.version_info >= (3, 9):
        with open(filepath, "rb") as input_file:
            file_contents = plistlib.load(input_file)
    else:
        file_contents = plistlib.readPlist(filepath)
    if file_contents["files"]:
        final_files = []
        for entry in file_contents["files"]:
            final_files.append(realpath(entry))
        file_contents["files"] = final_files
        with open(filepath, "wb") as output_file:
            if sys.version_info >= (3, 9):
                plistlib.dump(file_contents, output_file)
            else:
                plistlib.writePlist(file_contents, output_file)


def resolve_yaml_symlinks(filepath):
    """Resolve the symbolic links in YAML files to real file paths"""
    logging.info("Processing YAML file: %s", filepath)
    fields = [
        r"MainSourceFile:\s*",
        r"\s*-? FilePath:\s*",
    ]
    updated = 0
    line_to_write = []
    with open(filepath, "r", encoding="utf-8") as input_file:
        for line in input_file.readlines():
            for field in fields:
                pattern = f"({field})'(.*)'"
                match = re.match(pattern, line)
                if match:
                    field = match.group(1)
                    filename = match.group(2)
                    fullpath = realpath(filename)
                    if fullpath != filename:
                        updated += 1
                        replace = f"{field}'{fullpath}'\r\n"
                        line = replace
                    break
            line_to_write.append(line)
    if updated:
        logging.debug("     %d updated paths", updated)
        with open(filepath, "w", encoding="utf-8") as output_file:
            logging.debug("     saving...")
            output_file.writelines(line_to_write)


def resolve_symlinks(codechecker_files):
    """Change ".../execroot/apps" paths to absolute paths in data/* files"""
    stage("Resolve file paths in CodeChecker analyze output:")
    analyze_outdir = codechecker_files + "/data"
    logging.info(
        "Resolving file paths in CodeChecker analyze output at: %s",
        analyze_outdir,
    )
    files_processed = 0
    for root, _, files in os.walk(analyze_outdir):
        for filename in files:
            if re.search("clang-tidy", filename):
                filepath = os.path.join(root, filename)
                if os.path.splitext(filepath)[1] == ".plist":
                    resolve_plist_symlinks(filepath)
                elif os.path.splitext(filepath)[1] == ".yaml":
                    resolve_yaml_symlinks(filepath)
                files_processed += 1
    logging.info("Processed file paths in %d files", files_processed)


def update_file_paths(codechecker_files):
    """
    Fix bazel sandbox paths and resolve symbolic links
    in generated files to real paths
    """
    fix_bazel_paths(codechecker_files)
    resolve_symlinks(codechecker_files)


def parse(cfg):
    """Run CodeChecker parse commands"""
    stage("CodeChecker parse:")
    logging.info("CodeChecker parse -e json")
    codechecker_parse = (
        f"{cfg.codechecker_path} parse --config "
        f"{cfg.codechecker_config} {cfg.codechecker_files}/data"
    )
    # Save results to JSON file
    command = (
        f"{codechecker_parse} --export=json > "
        f"{cfg.codechecker_files}/result.json"
    )
    execute(cfg.codechecker_log, command, codes=[0, 2])
    # Save results as HTML report
    logging.info("CodeChecker parse -e html")
    command = (
        codechecker_parse
        + " --export=html --output="
        + cfg.codechecker_files
        + "/report"
    )
    execute(cfg.codechecker_log, command, codes=[0, 2])
    # Save results to text file
    logging.info("CodeChecker parse to text result")
    command = codechecker_parse + " > " + cfg.codechecker_files + "/result.txt"
    execute(cfg.codechecker_log, command, codes=[0, 2])
    logging.info(
        "Result:\n\n%s\n",
        read_file(cfg.codechecker_log, cfg.codechecker_files + "/result.txt"),
    )


def run(cfg):
    """Perform all steps for "bazel build" phase"""
    prepare(cfg.codechecker_files)
    analyze(cfg)
    parse(cfg)
    update_file_paths(cfg.codechecker_files)


def check_results(cfg):
    """Check/verify CodeChecker results"""
    stage("Checking result:")
    # Get results file and read it
    result_file = cfg.codechecker_files + "/result.txt"
    logging.info("Find CodeChecker results in bazel-out")
    logging.info("      all artifacts: %s/", cfg.codechecker_files)
    logging.info(
        "      HTML report:   %s/report/index.html", cfg.codechecker_files
    )
    logging.info("      result file:   %s", result_file)
    results = read_file(cfg.codechecker_log, result_file)
    logging.info("Results: \n\n%s\n", results)
    # Collect defect severities to detect
    if not valid_parameter(cfg.codechecker_severities):
        fail(
            cfg.codechecker_log,
            "CodeChecker defect severities are invalid: "
            f"{str(cfg.codechecker_severities)}",
        )
    severities = shlex.split(cfg.codechecker_severities)
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
        fail(cfg.codechecker_log, f"CodeChecker found defects:\n{conclusion}")


def test(cfg):
    """Perform all steps for "bazel test" phase"""
    check_results(cfg)


def main():
    """Main function"""
    cfg = parse_args()
    setup(cfg.verbosity, cfg.codechecker_log)
    input_data(cfg)
    try:
        if cfg.execution_mode == "Run":
            run(cfg)
        elif cfg.execution_mode == "Test":
            test(cfg)
        else:
            fail(
                cfg.codechecker_log,
                f"Wrong codechecker script mode: {cfg.execution_mode}",
            )
    # We want to fail explicitly here
    # pylint: disable=broad-exception-caught
    except Exception as error:
        logging.exception(error)
        fail(cfg.codechecker_log, "Caught Exception. Terminated")


if __name__ == "__main__":
    main()
