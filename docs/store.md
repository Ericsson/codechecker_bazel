Store
=====

## store()

The Bazel rule `store()` uploads CodeChecker analysis results to a remote
[CodeChecker server](https://codechecker.readthedocs.io/en/latest/web/user_guide/).
It collects the analysis output from one or more `codechecker_test()` targets
and runs
[`CodeChecker store`](https://github.com/Ericsson/codechecker/blob/master/docs/web/user_guide.md#store)
under the hood.

To use it, add the following to your BUILD file:

```python
load(
    "@rules_codechecker//:defs.bzl",
    "codechecker_test",
    "codechecker_store",
)
```

Create a `codechecker_test()` target and a `codechecker_store()` target that references it:

```python
codechecker_test(
    name = "codechecker",
    targets = [
        "your_target",
    ],
)

codechecker_store(
    name = "store",
    targets = [
        ":codechecker",
    ],
)
```

Then run it, passing the server URL and a run name:

```bash
bazel run //:store -- --url=http://localhost:8001/Default --name=my_run
```

### Parameters

| Parameter   | Description                                                                 |
|-------------|-----------------------------------------------------------------------------|
| `name`      | Name of the store target.                                                   |
| `targets`   | List of `codechecker_test()` targets whose results should be stored. |
| `toolchain` | Optional `codechecker_toolchain()` target. When set, tools from this target are used instead of Bazel's toolchain resolution. |
| `tags`      | Bazel tags. The `"store"` tag is added automatically.                       |

### Runtime arguments

The `--url` and `--name` arguments are required and passed after `--` on the
command line:

| Argument | Description                                                        |
|----------|--------------------------------------------------------------------|
| `--url`  | URL of the CodeChecker server product, e.g. `http://localhost:8001/Default`. |
| `--name` | Name of the analysis run on the server.                            |


### How it works

1. `codechecker_test()` exposes its analysis output via an output group.
2. `codechecker_store()` collects those files from all its target dependencies.
3. The report data is symlinked to a writable temporary directory (Bazel outputs
   are read-only and `CodeChecker store` needs write access).
4. `CodeChecker store` is executed against the specified server.

> [!NOTE]
> The `codechecker_store()` rule is an executable rule (`bazel run`), not a test rule.
> It is meant to be run manually when you want to publish results.
