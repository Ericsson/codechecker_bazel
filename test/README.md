# Tests:

## Running Tests

Our projects use both **`pytest`** and **`unittest`** frameworks.
You can run tests using either method.
The **`-vvv`** flag is used for **verbosity**, which provides more detailed output and is very helpful for debugging.

### To run all tests, use one of the following command:
* **Using Pytest:**
    ```bash
    pytest unit -vvv
    ```

* **Using Unittest:**
    ```bash
    python3 -m unittest discover unit -vvv
    ```

### Running a Subset of Tests
Specify the directory containing your desired tests. For example, to run tests in `my_test_dir`:

```bash
pytest unit/my_test_dir -vvv
# OR
python3 -m unittest discover unit/my_test_dir -vvv
```

## Adding New Unit Tests

1. **Create a Test Folder**  
   Inside the `unit` directory, create a folder for your new test. This folder should contain:
   - All source/header files needed for the test
   - `BUILD`
   - A python test script
   - `__init__.py`

2. **Creating the BUILD File**
    - Make sure that all failing test targets get the `"manual"` tag. For example:
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

2. **Creating the Test File**  
    - Your test script must follow the naming convention:
        ```text
        test_*.py
        ``` 
    - At the top of your test file, include the following snippet to correctly handle module imports:
        ```python
        from common.base import TestBase
        ```  
    - Create your test class by extending `TestBase` and implement your test methods.
> [!WARNING]
> You should include this line in your test class, this sets the current working directory:
> ```python
> __test_path__ = os.path.dirname(os.path.abspath(__file__))
> ```

**For a test template look into unit/template**

## Testing on open source projects

## Add a new open source project:

1. Create a folder in the foss folder with the name of the project.
2. The folder should contain:
    - init.sh

3. The init.sh script should:
  - Clone the test project into a folder, its path will be the first command line argument.
  - To ensure the project doesn't change over time, check out a specific tag or commit instead of a branch!
  - Copy the .bazelversion file, if it exists, from the root of codechecker_bazel into the projects directory.
  - Append the WORKSPACE.template file to the WORKSPACE file of the project.
  - Append the codechecker rules to the BUILD file of the project.
    - There can be only two targets, codechecker_test and per_file_test
