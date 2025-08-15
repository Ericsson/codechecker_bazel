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
    > Your current working directory will be `unit/common` for every action!

**For a test template look into unit/template**
