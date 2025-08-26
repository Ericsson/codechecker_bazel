#!{PythonPath}
"""
CodeChecker Bazel build & test wrapper script
"""

from __future__ import print_function
import getpass
import logging
import multiprocessing
import os
import plistlib
import re
import shlex
import subprocess
import sys


EXECUTION_MODE = "{Mode}"
VERBOSITY = "{Verbosity}"
CODECHECKER_PATH = "{codechecker_bin}"
CODECHECKER_SKIPFILE = "{codechecker_skipfile}"
CODECHECKER_CONFIG = "{codechecker_config}"
CODECHECKER_ANALYZE = "{codechecker_analyze}"
CODECHECKER_FILES = "{codechecker_files}"
CODECHECKER_LOG = "{codechecker_log}"
CODECHECKER_SEVERITIES = "{Severities}"
CODECHECKER_ENV = "{codechecker_env}"
COMPILE_COMMANDS = "{compile_commands}"

START_PATH = r"\/(?:(?!\.\s+)\S)+"
BAZEL_PATHS = {
    r"\/sandbox\/processwrapper-sandbox\/\S*\/execroot\/": "/execroot/",
    START_PATH + r"\/worker\/build\/[0-9a-fA-F]{16}\/root\/": "",
    START_PATH + r"\/[0-9a-fA-F]{32}\/execroot\/": "",
    # Running bazel with --spawn_strategy=processwrapper-sandbox
    # results in its path being wrongly replaced!
    # In that case the 1st then 3rd regex will match and leave the path in a
    # half baked state, this regex just finishes the job
    r"<string>bazel_codechecker\/": "<string>",
}


def fail(message, exit_code=1):
    """ Print error message and return exit code """
    logging.error(message)
    print()
    print("*" * 50)
    print("codechecker script execution FAILED!")
    if log_file_name():
        print("See: %s" % log_file_name())
        print("*" * 50)
        try:
            with open(log_file_name()) as log_file:
                print(log_file.read())
        except IOError:
            print("File not accessible")
    else:
        print(message)
    print("*" * 50)
    print()
    exit(exit_code)


def read_file(filename):
    """ Read text file and return its contents """
    if not os.path.isfile(filename):
        fail("File not found: %s" % filename)
    with open(filename) as handle:
        return handle.read()


def separator(method="info"):
    """ Print log separator line to logging.info() or other logging methods """
    getattr(logging, method)("#" * 23)


def stage(title, method="info"):
    """ Print stage title into log """
    separator(method)
    getattr(logging, method)("### " + title)
    separator(method)


def valid_parameter(parameter):
    """ Check if external parameter is defined and valid """
    if parameter is None:
        return False
    elif parameter and parameter[0] == "{":
        return False
    return True


def log_file_name():
    """ Check and return log file name """
    if valid_parameter(CODECHECKER_LOG):
        return CODECHECKER_LOG
    return None


def setup():
    """ Setup logging parameters for execution session """
    if VERBOSITY == "INFO":
        log_level = logging.INFO
    elif VERBOSITY == "WARN":
        log_level = logging.WARN
    else:
        log_level = logging.DEBUG
    log_format = "[codechecker] %(levelname)5s: %(message)s"

    if log_file_name():
        logging.basicConfig(filename=log_file_name(), level=log_level, format=log_format)
    else:
        logging.basicConfig(level=log_level, format=log_format)


def input_data():
    """ Print out input (external) parameters """
    stage("CodeChecker input data:", "debug")
    logging.debug("EXECUTION_MODE       : %s", str(EXECUTION_MODE))
    logging.debug("VERBOSITY            : %s", str(VERBOSITY))
    logging.debug("CODECHECKER_PATH     : %s", str(CODECHECKER_PATH))
    logging.debug("CODECHECKER_SKIPFILE : %s", str(CODECHECKER_SKIPFILE))
    logging.debug("CODECHECKER_CONFIG   : %s", str(CODECHECKER_CONFIG))
    logging.debug("CODECHECKER_ANALYZE  : %s", str(CODECHECKER_ANALYZE))
    logging.debug("CODECHECKER_FILES    : %s", str(CODECHECKER_FILES))
    logging.debug("CODECHECKER_LOG      : %s", str(CODECHECKER_LOG))
    logging.debug("CODECHECKER_ENV      : %s", str(CODECHECKER_ENV))
    logging.debug("COMPILE_COMMANDS     : %s", str(COMPILE_COMMANDS))
    logging.debug("")


def execute(cmd, env=None, codes=[0]):
    """ Execute CodeChecker commands """
    process = subprocess.Popen(
        cmd,
        env=env,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    if process.returncode not in codes:
        fail("\ncommand: %s\nstdout: %s\nstderr: %s\n" % (cmd, stdout, stderr))
    logging.debug("Executing: %s", cmd)
    # logging.debug("Output:\n\n%s\n", stdout)
    return stdout


def create_folder(path):
    """ Create folder structure for CodeChecker data files and reports """
    if not os.path.exists(path):
        os.makedirs(path)


def prepare():
    """ Prepare CodeChecker execution environment """
    stage("CodeChecker files:")
    logging.info("Creating folder: %s", CODECHECKER_FILES)
    create_folder(CODECHECKER_FILES)


def analyze():
    """ Run CodeChecker analyze command """
    stage("CodeChecker analyze:")

    env = os.environ
    if CODECHECKER_ENV:
        env_list = CODECHECKER_ENV.split("; ")
        if env_list:
            codechecker_env = dict(item.split("=", 1) for item in env_list)
            env.update(codechecker_env)
    if "PATH" not in env:
        env["PATH"] = "/bin"  # NOTE: this is workaround for CodeChecker 6.24.4
    logging.debug("env: %s", str(env))

    output = execute("%s analyzers --details" % CODECHECKER_PATH, env=env)
    logging.debug("Analyzers:\n\n%s", output)

    command = "%s analyze --skip=%s %s --output=%s/data --config %s %s" % (
        CODECHECKER_PATH,
        CODECHECKER_SKIPFILE,
        COMPILE_COMMANDS,
        CODECHECKER_FILES,
        CODECHECKER_CONFIG,
        CODECHECKER_ANALYZE,
    )
    # FIXME: Workaround "CodeChecker simply remove compiler-rt include path".
    # This can be removed once codechecker 6.16.0 is used.
    # command += " --keep-gcc-intrin"
    logging.info("Running CodeChecker analyze...")
    output = execute(command, env=env)
    logging.info("Output:\n\n%s\n", output)
    if output.find("- Failed to analyze") != -1:
        logging.error("CodeChecker failed to analyze some files")
        fail("Make sure that the target can be built first")


def fix_bazel_paths():
    """ Remove Bazel leading paths in all files """
    stage("Fix CodeChecker output:")
    folder = CODECHECKER_FILES
    logging.info("Fixing Bazel paths in %s", folder)
    counter = 0
    for root, _, files in os.walk(folder):
        for filename in files:
            fullpath = os.path.join(root, filename)
            with open(fullpath, "rt") as data_file:
                data = data_file.read()
                for pattern, replace in BAZEL_PATHS.items():
                    data = re.sub(pattern, replace, data)
            with open(fullpath, "w") as data_file:
                data_file.write(data)
            counter += 1
    logging.info("Fixed Bazel paths in %d files", counter)


def realpath(filename):
    """ Return real full absolute path for given filename """
    if os.path.exists(filename):
        real_file_name = os.path.abspath(os.path.realpath(filename))
        logging.debug("Updating %s -> %s", filename, real_file_name)
        filename = real_file_name
    return filename


def resolve_plist_symlinks(filepath):
    """ Resolve the symbolic links in plist files to real file paths """
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
    """ Resolve the symbolic links in YAML files to real file paths """
    logging.info("Processing YAML file: %s", filepath)
    fields = [
        r"MainSourceFile:\s*",
        r"\s*-? FilePath:\s*",
    ]
    updated = 0
    line_to_write = []
    with open(filepath, "r") as input_file:
        for line in input_file.readlines():
            for field in fields:
                pattern = "(%s)'(.*)'" % field
                match = re.match(pattern, line)
                if match:
                    field = match.group(1)
                    filename = match.group(2)
                    fullpath = realpath(filename)
                    if fullpath != filename:
                        updated += 1
                        replace = field + "'" + fullpath + "'\r\n"
                        line = replace
                    break
            line_to_write.append(line)
    if updated:
        logging.debug("     %d updated paths", updated)
        with open(filepath, "w") as output_file:
            logging.debug("     saving...")
            output_file.writelines(line_to_write)


def resolve_symlinks():
    """ Change ".../execroot/apps" paths to absolute paths in data/* files """
    stage("Resolve file paths in CodeChecker analyze output:")
    analyze_outdir = CODECHECKER_FILES + "/data"
    logging.info("Resolving file paths in CodeChecker analyze output at: %s", analyze_outdir)
    files_processed = 0
    for root, _, files in os.walk(analyze_outdir):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.splitext(filepath)[1] == ".plist":
                resolve_plist_symlinks(filepath)
            elif os.path.splitext(filepath)[1] == ".yaml":
                resolve_yaml_symlinks(filepath)
            files_processed += 1
    logging.info("Processed file paths in %d files", files_processed)
def update_file_paths():
    """ Fix bazel sandbox paths and resolve symbolic links in generated files to real paths """
    #fix_bazel_paths() # this is unnecessary
    resolve_symlinks()


def parse():
    """ Run CodeChecker parse commands """
    stage("CodeChecker parse:")
    logging.info("CodeChecker parse -e json")
    codechecker_parse = "{codechecker} parse --config {config} {output}".format(
        codechecker=CODECHECKER_PATH,
        config=CODECHECKER_CONFIG,
        output=CODECHECKER_FILES + "/data")
    # Save results to JSON file
    command = codechecker_parse + " --export=json > " + CODECHECKER_FILES + "/result.json"
    execute(command, codes=[0, 2])
    # logging.debug("JSON:\n\n%s\n", read_file(CODECHECKER_FILES + "/result.json"))
    # Save results as HTML report
    logging.info("CodeChecker parse -e html")
    command = codechecker_parse + " --export=html --output=" + CODECHECKER_FILES + "/report"
    execute(command, codes=[0, 2])
    # Save results to text file
    logging.info("CodeChecker parse to text result")
    command = codechecker_parse + " > " + CODECHECKER_FILES + "/result.txt"
    execute(command, codes=[0, 2])
    logging.info("Result:\n\n%s\n", read_file(CODECHECKER_FILES + "/result.txt"))


def run():
    """ Perform all steps for "bazel build" phase """
    prepare()
    analyze()
    parse()
    update_file_paths()


def check_results():
    """ Check/verify CodeChecker results """
    stage("Checking result:")
    # Get results file and read it
    result_file = CODECHECKER_FILES + "/result.txt"
    logging.info("Find CodeChecker results in bazel-out")
    logging.info("      all artifacts: %s/", CODECHECKER_FILES)
    logging.info("      HTML report:   %s/report/index.html", CODECHECKER_FILES)
    logging.info("      result file:   %s", result_file)
    results = read_file(result_file)
    logging.info("Results: \n\n%s\n", results)
    # Collect defect severities to detect
    if not valid_parameter(CODECHECKER_SEVERITIES):
        fail("CodeChecker defect severities are invalid: %s" % str(CODECHECKER_SEVERITIES))
    severities = shlex.split(CODECHECKER_SEVERITIES)
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
        found = re.findall(r"^%s .* (\d+)" % issue, results, re.M)
        defects = sum([int(number) for number in found])
        logging.debug("   %s : %s = %d", issue, str(found), defects)
        issues[issue] = defects
    logging.info("Defects: %s", str(issues))
    # Check collected defects
    passed = True
    conclusion = ""
    for issue in issues:
        if issues[issue] > 0:
            passed = False
            conclusion += "%15s : %d\n" % (issue, issues[issue])
    if passed:
        logging.info("No defects found by CodeChecker")
    else:
        fail("CodeChecker found defects:\n%s" % conclusion)


def test():
    """ Perform all steps for "bazel test" phase """
    check_results()


def main():
    """ Main function """
    setup()
    input_data()
    try:
        if EXECUTION_MODE == "Run":
            run()
        elif EXECUTION_MODE == "Test":
            test()
        else:
            fail("Wrong codechecker script mode: %s" % EXECUTION_MODE)
    except Exception as error:
        logging.exception(error)
        fail("Caught Exception. Terminated")


if __name__ == "__main__":
    main()
