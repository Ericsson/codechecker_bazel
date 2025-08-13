import unittest
import os
import sys

def run_all_tests(start_dir='./unit', verbosity=1):
    """
    Discovers and runs all Python unit tests within the specified
    start_directory and its subdirectories.

    Args:
        start_dir (str): The root directory to start test discovery from.
                         Defaults to the unit directory ('./unit').
    """
    print(f"Discovering tests starting from: {os.path.abspath(start_dir)}\n")

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir, pattern='*test*.py', top_level_dir=None)

    if not suite.countTestCases():
        print("No tests found. Ensure your test files are named '*test*.py' "
              "and contain unittest.TestCase classes.")
        return

    runner = unittest.TextTestRunner(verbosity=verbosity)

    print("Running tests...\n" + "="*50 + "\n")

    results = runner.run(suite)

    print("\n" + "="*50)
    print("Test Run Summary:")
    print(f"Total Tests Run: {results.testsRun}")
    if results.wasSuccessful():
        print("All tests passed!")
    else:
        print(f"Tests Failed: {len(results.failures)}")
        print(f"Tests Errored: {len(results.errors)}")
        if results.skipped:
            print(f"Tests Skipped: {len(results.skipped)}")


if __name__ == "__main__":
    verbosity = 1
    if "-vvv" in sys.argv:
        verbosity = 3
    run_all_tests(verbosity=verbosity)
