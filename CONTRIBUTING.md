Contributing
============

Thanks for your interest!

Here you can find information about:
- How to report a bug?
- How to submit a patch?


Reporting issues
----------------

Please always provide the following information:

1. Steps to reproduce
2. Expected behavior
3. Actual behavior


Development Environment
-----------------------

The following modules are needed for the development:

    module add git
    module add bazel/6
    module add clang/16
    module add python/3.11
    module add codechecker/6.26

    # Optional modules
    module add buildifier/4
    module add python/3.11-addons-pylint-2.14.5
    module add python/3.11-addons-pycodestyle-2.11.1

You can also add Bazel auto-completion by running the following:

    source $(dirname $(realpath $(which bazel)))/bazel-complete.bash


Directory structure
-------------------

Directory / File               | Description
------------------------------ | -----------
CONTRIBUTING.md                | This file
README.md                      | Main readme document
WORKSPACE                      | Declares Bazel workspaces for CodeChecker rules
src/                           | Rules for CodeChecker and compile_commands.json
src/BUILD                      | Declares and exports python scripts
src/clang.bzl                  | Clang-tidy and clang analyzer aspects and rules
src/clang_ctu.bzl              | PoC: Clang analyzer with CTU
src/code_checker.bzl           | PoC: CodeChecker analyze --file
src/codechecker.bzl            | Defines codechecker rules
src/codechecker_script.py      | CodeChecker Bazel build & test script template
src/compile_commands.bzl       | Compile commands (compilation database) aspect
src/compile_commands_filter.py | Filters compile_commands.json file
src/tools.bzl                  | Default Python toolchain and CodeChecker tool
test/                          | Tests for codechecker rules
test/BUILD                     | Defines codechecker rules tests
test/config.json               | Example of CodeChecker configuration
test/test.py                   | Functional and unit test runner
test/inc/                      | Directory for test C++ headers
test/inc/inc.h                 | Header file to check strip_include_prefix
test/src/                      | Directory for test C++ files
test/src/ctu.cc                | Simple library C++ code to check CTU
test/src/fail.cc               | Simple main() code which should FAIL
test/src/lib.cc                | Simple library C++ code to check dependencies
test/src/pass.cc               | Simple main() code which should PASS


Testing
-------

Before submitting any change please make sure all tests and checks are passed.

For a quick sanity check you can just run:

    python3 test/test.py


### Functional tests

Run functional tests in `test` directory:

    python3 test.py

For test debugging use `-vvv` option:

    python3 test.py -vvv

### Bazel tests

To run all bazel tests:

    bazel test ...

See CodeChecker output:

    bazel test ... --test_output=all

To check simple C++ example in `test` directory:

    bazel test :codechecker_pass --test_output=all
