Bazel Rules for CodeChecker
===========================

Bazel rules for CodeChecker and other tools for Code Analysis,
including Clang-tidy, Clang analyzer, generating compilation database
(`compile_commands.json`) and others.

> If you would like to report an issue or suggest a change
> please read [CONTRIBUTING.md](CONTRIBUTING.md).

### CodeChecker

CodeChecker is a static analysis infrastructure that conveniently manages static analyzer engines such as the Clang Static Analyzer, Clang-tidy, GCC Static Analyzer, CppCheck and Infer.

Read about CodeChecker:

* GitHub: https://github.com/Ericsson/codechecker
* Read the Docs: https://codechecker.readthedocs.io/

The main Bazel rule for CodeChecker is `codechecker_test()`.

### Clang-tidy

Clang-tidy is a fast static analyzer/linter for the C family of languages. This
repository provides Bazel aspect `clang_tidy_aspect` and rule `clang_tidy_test()`
to run clang-tidy natively (without CodeChecker).

Find more information about LLVM clang-tidy:

* LLVM: https://clang.llvm.org/extra/clang-tidy
* bazel_clang_tidy: https://github.com/erenon/bazel_clang_tidy

### Clang Static Analyzer

The Clang Static Analyzer (or `clang --analyze`) is among
the most sophisticated tools for C/C++ code analysis which implements
path-sensitive, inter-procedural analysis based on symbolic execution technique.
This repository provides the Bazel rule `clang_analyze_test()` which runs the
Clang Static Analyzer natively (without CodeChecker)

Find more information about LLVM Clang Static Analyzer:

* LLVM: https://clang.llvm.org/docs/ClangStaticAnalyzer.html

### Generating a compilation database

There is also a Bazel rule for generating a compilation database (compile_commands.json) via `compile_commands()`. The current implementation is Bazel native and doesn't use `CodeChecker log`.

Prerequisites
-------------

We need the following tools:

- Git 2 or newer (we use 2.36)
- Bazel in between version 4 and 6 (we recommend version 6.5.0)
- Clang 16 or newer (we use 16), we use clang-tidy
- Python 3.8 or newer (we use 3.11)
- CodeChecker 6.23 or newer (we use 6.23.0)

If, by chance, Environment Modules (https://modules.sourceforge.net/)
are available in your system, you can just add the following modules:

    module add git
    module add bazel/6
    module add clang/16
    module add python/3.11
    module add codechecker/6.23


How to use
----------

To use these rules you should first add `codechecker_bazel` as an
[external dependency](https://bazel.build/versions/6.5.0/external/overview#workspace-system)
to your `WORKSPACE` file:

```python
load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

git_repository(
    name = "bazel_codechecker",
    remote = "https://github.com/Ericsson/codechecker_bazel.git",
    branch = "main",
)

load(
    "@bazel_codechecker//src:tools.bzl",
    "register_default_codechecker",
    "register_default_python_toolchain",
)

register_default_python_toolchain()

register_default_codechecker()
```
## CodeChecker

### Standard CodeChecker invocation: `codechecker_test()`

`codechecker_test()` invokes CodeChecker the "standard way", as you'd call
it normally from the command line. The rule first generates a compilation
database on all targets given to the rule. Then, [`CodeChecker analyze`](https://github.com/Ericsson/codechecker/blob/master/docs/analyzer/user_guide.md#analyze)
is run on all translation units found in those targets.

> [!NOTE]
> Even though bazel is capable of incremental builds, if any files are
> rebuilt, this rule will reanalyze all translation units in all targets,
> even those that needed no rebuild.

To use `codechecker_test()` include it to your BUILD file:

```python
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker_test",
)
```

Create a `codechecker_test()` target by passing other targets you'd like CodeChecker to analyze:

<!-- TODO: Consider using https://github.com/bazelbuild/stardoc to document parameters -->
```python
codechecker_test(
    name = "your_codechecker_rule_name",
    targets = [
        "your_target",
    ],
)
```

Then invoke bazel:

```bash
bazel build ://your_codechecker_rule_name
```

You can find the analysis results in the `bazel-bin/` folder, on which you
can run [`CodeChecker store`](https://github.com/Ericsson/codechecker/blob/master/docs/web/user_guide.md#store)
or [`CodeChecker parse`](https://github.com/Ericsson/codechecker/blob/master/docs/analyzer/user_guide.md#parse):

```bash
CodeChecker parse bazel-bin/path/to/results
```

### Build-only CodeChecker analysis: `codechecker()`

This rule is functionally equivalent to `codechecker_test` but omits the test phase where either PASS or FAIL is printed.
You can include and use it similarly as well:

```python
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker"
)
```

### Multiplatform CodeChechecker analysis: `codechecker_suite()`

This rule is functionally equivalent to `codechecker_test` but allows for running on multiple platforms via the `platforms` parameter.
You can include and use it similarly as well:

```python
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker_suite"
)
```

### `codechecker_config()`

Using the Bazel rule `codechecker_config()` you can parse a CodeChecker [configuration file](https://github.com/Ericsson/codechecker/blob/master/docs/config_file.md).

First, include the rule in your BUILD file:

```python
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker_config"
)
```

Create a CodeChecker configuration file e.g. `config.json` (see example [here](https://github.com/Szelethus/codechecker_bazel/blob/readme_update/test/config.json)) and parse it using `codechecker_config()`. 

```python
codechecker_config(
    name = "your_codechecker_config",
    config_file = ":config.json"
)
```

Alternatively, you can assemble a CodeChecker configuration without a config file using the rule:

```python
codechecker_config(
    name = "your_codechecker_config",
    analyze = [
        "--enable=bugprone-dangling-handle",
        "--enable=bugprone-fold-init-type",
        "--enable=misc-non-copyable-objects",
        "--report-hash=context-free-v2",
    ]
)
```

You can now configure your `codechecker`, `codechecker_suite`, `codechecker_test` and `code_checker_test` targets using the above configuration:

```python
codechecker_test(
    name = "your_codechecker_rule_name",
    config = "your_codechecker_config",
    targets = [
        "your_target",
    ],
)
```

### Per-file CodeChecker analysis: `code_checker_test()`
> [!IMPORTANT]
> The rule is still in prototype status and is subject to changes without notice.
> You are free to experiment and report issues however!

Instead of a single CodeChecker call, the bazel rule `code_checker_test()` invokes
[`CodeChecker analyze`](https://github.com/Ericsson/codechecker/blob/master/docs/analyzer/user_guide.md#analyze)
_for each_ translation unit in the targets to analyze. The rule is intended to be
able to enable incremental analyses and dispatching  analysis jobs to remote build
agents.

To use `code_checker_test()` include it to your BUILD file:

```python
load(
    "@bazel_codechecker//src:code_checker.bzl",
    "code_checker_test",
)
```

Create a `code_checker_test()` target by passing other targets you'd like CodeChecker to analyze:

```python
code_checker_test(
    name = "your_code_checker_rule_name",
    targets = [
        "your_target",
    ],
)
```

```bash
bazel build ://your_code_checker_rule_name
```

The analysis results can be found and stored/parsed similarly to [`codechecker_test`](README.md#standard-codechecker-invocation-codechecker_test)

## CodeChecker independent rules

The following rules are _not_ using CodeChecker.

### Clang-tidy: `clang_tidy_aspect` and `clang_tidy_test()`

The Bazel rule `clang_tidy_test` runs clang-tidy natively without CodeChecker. To use it, add the following to your BUILD file:

```python
load(
    "@bazel_codechecker//src:clang.bzl",
    "clang_tidy_test",
)

clang_tidy_test(
    name = "your_rule_name",
    targets = [
        "your_target",
    ],
)
```

The Bazel aspect `clang_tidy_aspect` uses `clang_tidy_test` under the hood, but can be invoked from the command line by passing the following parameter to Bazel build/test: `--aspects @bazel_codechecker//src:clang.bzl%clang_tidy_aspect`.

### Clang Static Analyzer: `clang_analyze_test()` and `clang_ctu_test`

The Bazel rule `clang_analyze_test` runs The Clang Static Analyzer natively without CodeChecker. To use it, add the following to your BUILD file:

```python
load(
    "@bazel_codechecker//src:clang.bzl",
    "clang_analyze_test",
)

clang_analyze_test(
    name = "your_rule_name",
    targets = [
        "your_target",
    ],
)
```

> [!IMPORTANT]
> You are welcome to experiment with `clang_ctu_test`, but it is recommended
> (as per [the official documentation](https://clang.llvm.org/docs/analyzer/user-docs/CrossTranslationUnit.html))
> to use CTU with CodeChecker. Please bear with us while we getting it to work!

The Bazel rule `clang_analyze_test` runs The Clang Static Analyzer with [cross translation unit analysis](https://clang.llvm.org/docs/analyzer/user-docs/CrossTranslationUnit.html) analysis without CodeChecker. To use it, add the following to your BUILD file:

```python
load(
    "@bazel_codechecker//src:clang_ctu.bzl",
    "clang_ctu_test",
)

clang_ctu_test(
    name = "your_code_checker_rule_name",
    targets = [
        "your_target",
    ],
)
```

### Generating a compilation database: `compile_commands()`

As generating a compilation database for C/C++ is a known pain point for bazel, this repository defines the Bazel rule `compile_commands()` rule which can be used indendently of CodeChecker. The implementation is basen on https://github.com/grailbio/bazel-compilation-database with some fixes on some tricky edge cases. To use it, include the following in your BUILD file:

```python
load(
    "@bazel_codechecker//src:compile_commands.bzl",
    "compile_commands",
)
```

Then use `compile_commands()` rule passing build targets:

```python
compile_commands(
    name = "your_compile_commands_rule_name",
    targets = [
        "your_target",
    ],
)
```
You can find the generated `compile_commands.json` under `bazel-bin/`.

Examples
--------

In [test/BUILD](test/BUILD) you can find examples for `codechecker_test()`
and for `compile_commands()` rules.

For instance see `codechecker_pass` and `compile_commands_pass`.

Run all test Bazel targets:

    bazel test ...

After that you can find all artifacts in `bazel-bin` directory:

    # All codechecker_pass artifacts
    ls bazel-bin/test/codechecker_pass/
    
    # compile_commands.json for compile_commands_pass
    cat bazel-bin/test/compile_commands_pass/compile_commands.json

To run `clang_tidy_aspect` on all C/C++ code:

    bazel build ... --aspects @bazel_codechecker//src:clang.bzl%clang_tidy_aspect --output_groups=report
