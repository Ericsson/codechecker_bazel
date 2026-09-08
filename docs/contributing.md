Contributing
============

Everything you need to work on `rules_codechecker` itself.
For using the rules in your project see [Getting Started](getting-started).


## Reporting issues

Navigate to the issues tab in GitHub, click on "New Issue", then select and
fill out the appropriate template. If any of the fields are confusing, feel
free to submit and we will help you to iron out the rest.

Please open an issue before a pull request, the
[pull request template](https://github.com/Ericsson/rules_codechecker/blob/main/.github/pull_request_template.md)
asks for the issue it addresses.


## Development environment

Everything is built and tested inside the Micromamba environment, which brings
its own Bazel, CodeChecker, Clang and Python:

```bash
source .ci/micromamba/init.sh
```

The script installs Micromamba under `.ci/micromamba/`, creates the
environment and activates it. It has to be sourced, a subshell cannot activate
anything in your shell. Options select the tool versions:

```bash
source .ci/micromamba/init.sh --bazel=8.5.1 --codechecker=6.27.3
source .ci/micromamba/init.sh --force          # recreate the environment
bash   .ci/micromamba/init.sh                  # only create, activate later
```

See [.ci/micromamba/README.md](https://github.com/Ericsson/rules_codechecker/blob/main/.ci/micromamba/README.md)
for the details, and `.ci/mise/README.md` for the Mise based alternative.

Bazel auto-completion, once the environment is active:

```bash
source $(dirname $(realpath $(which bazel)))/bazel-complete.bash
```


## Directory structure

```tree
rules_codechecker/
├── .ci/
│   ├── micromamba/                 Development and CI environment
│   └── mise/                       Alternative dev environment
├── docs/                           This documentation
├── src/                            Implementation of the rules
│   ├── BUILD                       Exports the python scripts
│   ├── clang.bzl                   Clang-Tidy and Clang Analyzer rules
│   ├── clang_ctu.bzl               Clang Analyzer with CTU (PoC)
│   ├── codechecker.bzl             CodeChecker rules
│   ├── codechecker_config.bzl      CodeChecker configuration rule
│   ├── codechecker_script.py       Wrapper around CodeChecker
│   ├── codechecker_toolchain.bzl   Toolchain rule and provider
│   ├── common.bzl                  Helpers shared by the rules
│   ├── compile_commands.bzl        Compilation database aspect
│   ├── compile_commands_filter.py  Filters compile_commands.json
│   ├── per_file.bzl                CodeChecker analyze --file (PoC)
│   ├── per_file_script.py          Wrapper around analyze --file
│   └── tools.bzl                   Default tools and module extension
├── test/                           Tests for the rules
│   ├── buildifier/                 Starlark linting
│   ├── common/                     Test base classes and helpers
│   ├── foss/                       Rules on open source projects
│   └── unit/                       Unit tests
├── BUILD                           Toolchain type and default toolchain
├── MODULE.bazel                    Module and its dependencies
└── defs.bzl                        Public API for our users
```


## Testing

Run all of these inside the Micromamba environment before submitting:

```bash
pylint .
bazel test //...
pytest test
```

Or let one script do the whole round:

```bash
.ci/micromamba/run_tests.sh
```

On how to run or add a new test, see
[test/README.md](https://github.com/Ericsson/rules_codechecker/blob/main/test/README.md).

### Linting Python with Bazel

Python targets are linted through a per-target Bazel macro.
Add a `pylint(...)` target next to a top-level
`py_binary`/`py_library`/`py_test`:

```starlark
load("//test/pylint:pylint_test.bzl", "pylint")

pylint(
    name = "pylint",
    targets = [":my_py_binary"],
)
```

It lints the targets and their dependencies (except pip packages)
These targets run as part of `bazel test //...` (tagged `pylint`).


## Submitting a patch

Fill out the pull request template: why the change is needed, what it does, and
the issue it addresses. Keep the public API in mind: anything added to
[defs.bzl](public-api) is a promise to our users, anything under `src/` is not.

If you are a new contributor and the template is confusing, feel free to submit
the pull request and we will help you iron it out.
