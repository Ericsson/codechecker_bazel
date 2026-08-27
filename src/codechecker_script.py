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

import argparse
import logging
import os
import plistlib
import re
import shlex
import subprocess
import sys


START_PATH = r"\/(?:(?!\.\s+)\S)+"
BAZEL_PATHS = {
    r"\/sandbox\/processwrapper-sandbox\/\S*\/execroot\/": "/execroot/",
    START_PATH + r"\/worker\/build\/[0-9a-fA-F]{16}\/root\/": "",
    START_PATH + r"\/[0-9a-fA-F]{32}\/execroot\/": "",
}


def parse_args(argv=None):
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="CodeChecker Bazel Wrapper")

    parser.add_argument("--mode", required=True, help="Execution mode")
    parser.add_argument("--verbosity", default="INFO", help="Log level")
    parser.add_argument("--codechecker", required=True,
                        help="CodeChecker path")
    parser.add_argument("--clang-tidy", help="clang-tidy path")
    parser.add_argument("--clang", help="clang path")
    parser.add_argument("--commands", dest="compile_commands",
                        help="compile_commands.json file")
    parser.add_argument("--skip", help="Skipfile path")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument("--analyze", default="", help="Analysis options")
    parser.add_argument("--output",
                        help="Directory where CodeChecker saves results")
    parser.add_argument("--log", help="Log file path")
    parser.add_argument("--env", action="append", default=[],
                        help="Environment variable, as KEY=VALUE")
    parser.add_argument("--severities", help="List of severities to fail on")
    args = parser.parse_args(argv)

    # Tools are symlinks in the runfiles tree
    args.codechecker = os.path.realpath(args.codechecker)
    if args.clang:
        args.clang = os.path.realpath(args.clang)
    if args.clang_tidy:
        args.clang_tidy = os.path.realpath(args.clang_tidy)
    return args


def fail(codechecker_log, message, exit_code=1):
    """Print error message and return exit code"""
    logging.error(message)
    print()
    print("*" * 50)
    print("codechecker script execution FAILED!")
    if codechecker_log:
        print(f"See: {codechecker_log}")
        print("*" * 50)
        try:
            with open(codechecker_log, encoding="utf-8") as log_file:
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


def setup(verbosity, codechecker_log):
    """Setup logging parameters for execution session"""
    if verbosity == "INFO":
        log_level = logging.INFO
    elif verbosity == "WARN":
        log_level = logging.WARN
    else:
        log_level = logging.DEBUG
    log_format = "[codechecker] %(levelname)5s: %(message)s"

    if codechecker_log:
        logging.basicConfig(
            filename=codechecker_log,
            level=log_level,
            format=log_format)
    else:
        logging.basicConfig(level=log_level, format=log_format)


def input_data(args):
    """Print out input (external) parameters"""
    stage("CodeChecker input data:", "debug")
    logging.debug("mode             : %s", args.mode)
    logging.debug("verbosity        : %s", args.verbosity)
    logging.debug("codechecker      : %s", args.codechecker)
    logging.debug("clang            : %s", args.clang)
    logging.debug("clang_tidy       : %s", args.clang_tidy)
    logging.debug("compile_commands : %s", args.compile_commands)
    logging.debug("skip             : %s", args.skip)
    logging.debug("config           : %s", args.config)
    logging.debug("analyze          : %s", args.analyze)
    logging.debug("output           : %s", args.output)
    logging.debug("log              : %s", args.log)
    logging.debug("env              : %s", args.env)
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
            fail(codechecker_log,
                 f"\ncommand: {cmd}\nstdout: {stdout}\nstderr: {stderr}\n")
        logging.debug("Executing: %s", cmd)
        # logging.debug("Output:\n\n%s\n", stdout)
    return stdout


def build_env(args):
    """Return environment"""
    env = os.environ.copy()
    for entry in args.env:
        if "=" not in entry:
            fail(args.log, f"Environment entry is not KEY=VALUE: {entry}")
        key, value = entry.split("=", 1)
        env[key] = value
    # Note: This is a workaround, CodeChecker requires the PATH to be set
    if "PATH" not in env:
        env["PATH"] = "/bin"
    if env.get("CC_ANALYZERS_FROM_PATH"):
        logging.debug("CC_ANALYZERS_FROM_PATH is set: use analyzers from PATH")
    elif env.get("CC_ANALYZER_BIN"):
        logging.debug("CC_ANALYZER_BIN is set by the configuration")
    else:
        env["CC_ANALYZER_BIN"] = (
            f"clangsa:{args.clang};clang-tidy:{args.clang_tidy}"
        )
    logging.debug("env: %s", str(env))
    return env


def prepare(codechecker_files):
    """Prepare CodeChecker execution environment"""
    stage("CodeChecker files:")
    logging.info("Creating folder: %s", codechecker_files)
    if not os.path.exists(codechecker_files):
        os.makedirs(codechecker_files)


def analyze(args):
    """Run CodeChecker analyze command"""
    stage("CodeChecker analyze:")
    env = build_env(args)
    output = execute(
        args.log,
        f"{args.codechecker} analyzers --details",
        env=env,
    )
    logging.debug("Analyzers:\n\n%s", output)

    command = (
        f"{args.codechecker} analyze "
        f"--skip={args.skip} "
        f"{args.compile_commands} "
        f"--output={args.output}/data "
        f"--config {args.config} "
        f"{args.analyze}"
    )
    # FIXME: Workaround "CodeChecker simply remove compiler-rt include path".
    # This can be removed once codechecker 6.16.0 is used.
    # command += " --keep-gcc-intrin"
    logging.info("Running CodeChecker analyze...")
    output = execute(args.log, command, env=env)
    logging.info("Output:\n\n%s\n", output)
    if output.find("- Failed to analyze") != -1:
        logging.error("CodeChecker failed to analyze some files")
        fail(args.log, "Make sure that the target can be built first")


def fix_path_with_regex(data):
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
    logging.info("Processing plist file: %s", filepath)
    with open(filepath, "rb") as input_file:
        file_contents = plistlib.load(input_file)
    if file_contents["files"]:
        final_files = []
        for entry in file_contents["files"]:
            final_files.append(realpath(entry))
        file_contents["files"] = final_files
        with open(filepath, "wb") as output_file:
            plistlib.dump(file_contents, output_file)


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
    logging.info("Resolving file paths in CodeChecker analyze output at: %s",
                 analyze_outdir)
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


def parse(args):
    """Run CodeChecker parse commands"""
    stage("CodeChecker parse:")
    env = build_env(args)
    logging.info("CodeChecker parse -e json")
    codechecker_parse = (
        f"{args.codechecker} parse --config "
        f"{args.config} {args.output}/data"
    )
    # Save results to JSON file
    command = (
        f"{codechecker_parse} --export=json > "
        f"{args.output}/result.json"
    )
    execute(args.log, command, env=env, codes=[0, 2])
    # Save results as HTML report
    logging.info("CodeChecker parse -e html")
    command = (
        codechecker_parse
        + " --export=html --output="
        + args.output
        + "/report"
    )
    execute(args.log, command, env=env, codes=[0, 2])
    # Save results to text file
    logging.info("CodeChecker parse to text result")
    result_file = args.output + "/result.txt"
    command = codechecker_parse + " > " + result_file
    execute(args.log, command, env=env, codes=[0, 2])
    logging.info("Result:\n\n%s\n", read_file(args.log, result_file))


def run(args):
    """Perform all steps for "bazel build" phase"""
    prepare(args.output)
    analyze(args)
    parse(args)
    update_file_paths(args.output)


def check_results(args):
    """Check/verify CodeChecker results"""
    stage("Checking result:")
    # Get results file and read it
    result_file = args.output + "/result.txt"
    logging.info("Find CodeChecker results in bazel-bin")
    logging.info("      all artifacts: %s/", args.output)
    logging.info("      HTML report:   %s/report/index.html", args.output)
    logging.info("      result file:   %s", result_file)
    results = read_file(args.log, result_file)
    logging.info("Results: \n\n%s\n", results)
    # Collect defect severities to detect
    if args.severities is None:
        fail(args.log,
             "CodeChecker defect severities are invalid: "
             f"{str(args.severities)}")
    severities = shlex.split(args.severities)
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
        fail(args.log, f"CodeChecker found defects:\n{conclusion}")


def test(args):
    """Perform all steps for "bazel test" phase"""
    check_results(args)


def main():
    """Main function"""
    args = parse_args()
    setup(args.verbosity, args.log)
    input_data(args)
    try:
        if args.mode == "Run":
            run(args)
        elif args.mode == "Test":
            test(args)
        else:
            fail(args.log, f"Wrong codechecker script mode: {args.mode}")
    # We want to fail explicitly here
    # pylint: disable=broad-exception-caught
    except Exception as error:
        logging.exception(error)
        fail(args.log, "Caught Exception. Terminated")


if __name__ == "__main__":
    main()
