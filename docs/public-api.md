Public API
==========

Everything below is loaded from `@rules_codechecker//:defs.bzl`.
Anything under `@rules_codechecker//src` is implementation and may change
without notice.

```python
load("@rules_codechecker//:defs.bzl", "codechecker_test")
```


## Rules

| Symbol | Purpose |
|-------------------------|-----------------------------------------------------|
| [`codechecker_test()`](codechecker#codechecker_test) | run CodeChecker on the given targets |
| [`codechecker_suite()`](codechecker#codechecker_suite) | run CodeChecker for several platforms |
| [`codechecker_config()`](codechecker#codechecker_config) | assemble a CodeChecker configuration |
| [`clang_tidy_test()`](clang#clang_tidy_test) | run clang-tidy without CodeChecker |
| [`clang_analyze_test()`](clang#clang_analyze_test) | run the Clang Static Analyzer without CodeChecker |
| [`compile_commands()`](compile-commands#compile_commands) | generate `compile_commands.json` |
| [`codechecker_store()`](store#store) | upload analysis results to a CodeChecker server |
| [`codechecker_toolchain()`](toolchains#providing-your-own-tools) | provide your own tools |


## Building blocks

For projects writing their own rules on top of these:

| Symbol | Purpose |
|---------------------------|---------------------------------------------------|
| [`compile_commands_aspect`](compile-commands#compile_commands_aspect) | collect sources and compile commands of a target |
| [`SourceFilesInfo`](compile-commands#sourcefilesinfo) | provider returned by the aspect |
| [`platforms_transition`](compile-commands#platforms_transition) | transition to the platform in the rule's `platform` attribute |
| [`get_platform_alias()`](codechecker#get_platform_alias) | short platform name used in `codechecker_suite()` test names |


## Labels

| Label | Purpose |
|-------------------------------------------|-----------------------------------|
| `@rules_codechecker//:toolchain_type` | toolchain type of your own toolchain |
| `@rules_codechecker//:default_toolchain` | the toolchain using tools from PATH |
