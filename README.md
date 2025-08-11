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
repository provides Bazel aspect `clang_tidy_aspect()` and rule `clang_tidy_test()`
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
- Bazel 6, not yet bazel 7 (we recommend version 6.5.0)
- Clang 16 or newer (we use 16), we use clang-tidy
- Python 3.8 or newer (we use 3.11)
- CodeChecker 6.26 or newer (we use 6.26.0)

If, by chance, Environment Modules (https://modules.sourceforge.net/)
are available in your system, you can just add the following modules:

    module add git
    module add bazel/6
    module add clang/16
    module add python/3.11
    module add codechecker/6.26


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
bazel test ://your_codechecker_rule_name
# Or, as a part of the rest of the testsuite
bazel test ...
```

You can find the analysis results in the `bazel-bin/` folder, on which you
can run [`CodeChecker store`](https://github.com/Ericsson/codechecker/blob/master/docs/web/user_guide.md#store)
or [`CodeChecker parse`](https://github.com/Ericsson/codechecker/blob/master/docs/analyzer/user_guide.md#parse).
The precise output path to the directory can vary, but you should look for `your_codechecker_rule_name/codechecker-files/data`.
In simpler cases, something like the following:

```bash
CodeChecker parse bazel-bin/your_codechecker_rule_name/codechecker-files/data
CodeChecker store bazel-bin/your_codechecker_rule_name/codechecker-files/data -n "Run name"
```

<!-- For now, we consider codechecker() to be an internal rule.

### Build-only CodeChecker analysis: `codechecker()`

This rule is functionally equivalent to `codechecker_test()` but omits the test phase where either PASS or FAIL isc printed.
You can include and use it similarly as well:

```python
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker"
)
```

-->

### Multi-platform CodeChecker analysis: `codechecker_suite()`
_TODO: Describe this rule: see issue [#44](https://github.com/Ericsson/codechecker_bazel/issues/44)._
<!--
This rule is functionally equivalent to `codechecker_test()` but allows for running on multiple platforms via the `platforms` parameter.
You can include and use it similarly as well:

```python
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker_suite"
)
```
-->
### `codechecker_config()`

Using the Bazel rule `codechecker_config()` you can utilize a CodeChecker [configuration file](https://github.com/Ericsson/codechecker/blob/master/docs/config_file.md).

First, include the rule in your BUILD file:

```python
load(
    "@bazel_codechecker//src:codechecker.bzl",
    "codechecker_config"
)
```

Create a CodeChecker configuration file e.g. `config.json` (see example [test/config.json](test/config.json)) and parse it using `codechecker_config()`.

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

You can now configure your `codechecker_suite()`, `codechecker_test()` and `code_checker_test()` targets using the above configuration:

```python
codechecker_test(
    name = "your_codechecker_rule_name",
    config = "your_codechecker_config",
    targets = [
        "your_target",
    ],
)
```

## CodeChecker independent rules

The following rules are _not_ using CodeChecker.

### Clang-tidy: `clang_tidy_aspect()` and `clang_tidy_test()`

The Bazel rule `clang_tidy_test()` runs clang-tidy natively without CodeChecker. To use it, add the following to your BUILD file:

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

You can also run clang-tidy via the Bazel aspect `clang_tidy_aspect()` that can be invoked from the command line by passing the following parameter to Bazel build/test: `--aspects @bazel_codechecker//src:clang.bzl%clang_tidy_aspect`:

```bash
bazel build ... --aspects @bazel_codechecker//src:clang.bzl%clang_tidy_aspect --output_groups=report
```

### Clang Static Analyzer: `clang_analyze_test()`

The Bazel rule `clang_analyze_test()` runs The Clang Static Analyzer natively without CodeChecker. To use it, add the following to your BUILD file:

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

### Generating a compilation database: `compile_commands()`

As generating a compilation database for C/C++ is a known pain point for bazel, this repository defines the Bazel rule `compile_commands()` rule which can be used independently of CodeChecker. The implementation is based on https://github.com/grailbio/bazel-compilation-database with some fixes on some tricky edge cases. To use it, include the following in your BUILD file:

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

## Experimental rules

### Per-file CodeChecker analysis: `code_checker_test()`
> [!IMPORTANT]
> The rule is still in prototype status and is subject to changes or removal without notice. See [#31](https://github.com/Ericsson/codechecker_bazel/issues/31).
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

Create a `code_checker_test()` target by passing targets you'd like CodeChecker to analyze, similarly to `codechecker_test()`:

```python
code_checker_test(
    name = "your_code_checker_rule_name",
    targets = [
        "your_target",
    ],
)
```

You can find the analysis results in the `bazel-bin/` folder similarly to [`codechecker_test()`](README.md#standard-codechecker-invocation-codechecker_test),
only without the `codechecker-files` directory. In simple cases, the results directory can be found and parsed as follows:

```bash
CodeChecker parse bazel-bin/your_code_checker_rule_name/data
CodeChecker store bazel-bin/your_code_checker_rule_name/data -n "Run name"
```

### Cross-translation unit analysis via the Clang Static Analyzer: `clang_ctu_test()`
> [!IMPORTANT]
> The rule is still in prototype status and is subject to changes or removal without notice. See [#32](https://github.com/Ericsson/codechecker_bazel/issues/32).
> We are also actively pursuing better CTU support _using_ CodeChecker.

The Bazel rule `clang_analyze_test()` runs The Clang Static Analyzer with [cross translation unit analysis](https://clang.llvm.org/docs/analyzer/user-docs/CrossTranslationUnit.html) analysis without CodeChecker. To use it, add the following to your BUILD file:

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

Examples
--------

In [test/BUILD](test/BUILD) you can find examples for `codechecker_test()`
and for `compile_commands()` rules.

For instance see targets `codechecker_pass` and `compile_commands_pass`.

Run all test Bazel targets:

    bazel test ...

After that you can find all artifacts in `bazel-bin` directory:

    # All codechecker_pass artifacts
    ls bazel-bin/test/codechecker_pass/
    
    # compile_commands.json for compile_commands_pass
    cat bazel-bin/test/compile_commands_pass/compile_commands.json

To run `clang_tidy_aspect()` on all C/C++ code:

    bazel build ... --aspects @bazel_codechecker//src:clang.bzl%clang_tidy_aspect --output_groups=report
