# Tests:

## Running Tests

Our projects use both **`bazel tests`** and **`pytest`**.
You can run bazel tests with: `bazel test //...`.
For more verbosity in python tests use **`-vvv`** or **`--log-cli-level=DEBUG`** for pytest.

### To run all python tests, use one of the following command:
* **Using Pytest:**
    ```bash
    pytest unit -vvv
    ```

* **Using Unittest:**
    ```bash
    python3 -m unittest discover unit -vvv
    ```


## Adding New Tests,

### Create a Test Folder
   Inside the `unit` directory, create a folder for your new test. This folder should contain:
   - All source/header files needed for the test
   - `BUILD`

---
### Create a skylib test

With skylib we can test anything that does not use the output of
`ctx.actions.run` actions (i.e. anything known at Bazel's analysis time).
Skylib provides two different kinds of tests: **unit tests** and
**analysis tests**.

For more in depth information check the skylib documentation for [analysis](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/analysis_test_doc.md) and [unit tests](https://github.com/bazelbuild/bazel-skylib/blob/main/docs/unittest_doc.md).

- **Unit tests** assert on a single Starlark function — call it with
    known inputs and check the return value. (See example in: `test/unit/basic/analysis_test.bzl`.)
- **Analysis tests** build a real Bazel target and then inspect the
    providers it returns (e.g. `DefaultInfo`, `CcInfo`, or custom
    providers) without executing any actions. (See example in: `test/unit/basic/unit_test.bzl`.)

Both are created in a `.bzl` file, instantiated from a `BUILD` file,
and run with `bazel test`.

---
### Creating unit tests asserting on the output of a rule

We can test the output of `ctx.actions.run` actions using the `unit_test` macro found in `test/unit/unit_test.bzl`.
You may use the tests under `test/unit/basic` as template.
- Create the `cc_binary/library` targets.
- Create the `codechecker_test` targets.
- Create `unit_test` targets to assert on the outputs of the codechecker targets. (See `unit/unit_test.bzl` for documentation)
- Make sure that all failing `codechecker_test` targets get the `"manual"` tag. For example:
```
# This is a test I expect to fail
codechecker_test(
    name = "codechecker_fail",
    tags = [
        "manual",
    ],
    targets = [
        "test_fail",
    ],
)
```
- Tip: To test these failing tests, create a unit_test target and assert the bug being found.

---
### Create a custom python test if you must
    
    In case you are writing integration tests, or tests that cannot be satisfied by the previous two solutions,
    create a custom `py_test` target. To make thing nicer wrap the py_test into a macro like with `unit_test.blz`.

    For reference you may use:
    - `test/unit/unit_test.bzl`
    - `test/foss`
    - `test/caching`

## Testing on open source projects

You can run all FOSS test with `bazel test //test/foss:*`.

## Add a new open source project:

Add a new `foss_test` target to the BUILD file in `test/foss`.
For each foss test you have to:
    - Give an url to an archive of the codebase (get it from the releases page).
    - In case the name of the target you want to test on differs from the name given to the test, define it with `target`.
    - Define which tests should be run. (possible values are: `":codechecker_per_file"`, `":codechecker_test"`, `":compile_commands"`)

Example:
```python
foss_test(
    name = "cpuinfo_bazel",
    target = "cpuinfo",
    tests = [
        ":codechecker_per_file",
        ":codechecker_test",
        ":compile_commands",
    ],
    url = "https://github.com/pytorch/cpuinfo/archive/66ee79c0.tar.gz",
)
```
