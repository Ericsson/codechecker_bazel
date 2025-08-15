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
   - A `BUILD` file
   - A python test script
   - An `__init__.py`

2. **Creating the Test File**  
   Your test script must follow the naming convention:
   ```text
   test_*.py
   ```

3. **Set Up Python Path**  
   At the top of your test file, include the following snippet to correctly handle module imports:
   ```python
   import os
   import sys

   # Python path magic, necessary to avoid module errors
   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   from common.base import TestBase
   ```

4. **Write the Test Class**  
   Create your test class by extending `TestBase` and implement your test methods.

**A simple test class would look like this:**
```python
"""
TODO: Describe what this file does
"""
import os
import sys
import unittest
# Python path magic, necessary to avoid module errors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import TestBase

# TODO: fix folder name
BAZEL_BIN_DIR = os.path.join("../../..", "bazel-bin", "test", 
                                    "unit", "my_test_folder")
BAZEL_TESTLOGS_DIR = os.path.join("../../..", "bazel-testlogs", "test", 
                                    "unit", "my_test_folder")

class TestTemplate(TestBase):
    """TODO: Add a description"""

    def setUp(self):
        """TODO: Define clean up before every test"""
        super().setUp()
        self.check_command("bazel clean")

    def test_template(self):
        """Test: TODO: describe your test"""
        self.fail(f"Test not implemented")


if __name__ == "__main__":
    unittest.main(buffer=True) 
``` 