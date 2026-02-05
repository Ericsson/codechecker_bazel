Contributing
============


Reporting issues
----------------

Please navigate to the issues tab in GitHub, and click on "New Issue", and select and fill out the appropriate template. If any of the fields are confusing, feel free to submit and we will help you to iron out the rest.


Development Environment
-----------------------

The following additional modules the ones found in the [README](README.md) are needed for the development:

    # Optional modules
    module add buildifier/4
    module add python/3.11-addons-pylint-2.14.5
    module add python/3.11-addons-pycodestyle-2.11.1

You can also add Bazel auto-completion by running the following:

    source $(dirname $(realpath $(which bazel)))/bazel-complete.bash


Directory structure overview
-------------------

Directory / File               | Description
------------------------------ | -----------
src/                           | Rules for CodeChecker and compile_commands.json
src/BUILD                      | Declares and exports python scripts
src/clang.bzl                  | Clang-tidy and clang analyzer aspects and rules
src/clang_ctu.bzl              | PoC: Clang analyzer with CTU
src/per_file.bzl               | PoC: CodeChecker analyze --file
src/per_file_script.py         | Wrapper around 'CodeChecker analyze --file'
src/codechecker.bzl            | Defines codechecker rules
src/codechecker_script.py      | Wrapper around 'CodeChecker analyze'
src/compile_commands.bzl       | Compile commands (compilation database) aspect
src/compile_commands_filter.py | Filters compile_commands.json file
src/tools.bzl                  | Default Python toolchain and CodeChecker tool
test/                          | Tests for codechecker rules
test/unit/                     | Unit tests
test/foss/                     | Scripts for automatically running these rules on select free open source software
test/common/                   | Collection of test base classes and convenience functions
test/test.sh                   | Functional and unit test runner


Submitting a patch and testing
-------

Before submitting any changes please make sure all tests and checks are passed, pylint doesn't show warnings on new code, and fill out the Pull Request template. If you are a new contributor, and the template is confusing, feel free to submit the PR and we will help you iron it out! On how to run or add a new test, please see [test/README.md](test/README.md).
