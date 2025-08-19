"""
Base for unit and functional tests
"""

import logging
import os
import re
import shlex
import subprocess
import unittest
import sys


class TestBase(unittest.TestCase):
    """Unittest base abstract class"""

    # This variable must be overwritten in each subclass!
    __test_path__: str = os.path.abspath(__file__)

    @classmethod
    def setUpClass(cls):
        """Load module, save environment"""
        # Enable debug logs for tests if "super verbose" flag is provided
        if "-vvv" in sys.argv:
            logging.basicConfig(
                level=logging.DEBUG, format="[TEST] %(levelname)5s: %(message)s"
            )
        # Move to test dir
        cls.test_dir = cls.__test_path__
        os.chdir(cls.test_dir)
        # Save environment and location
        cls.save_env = os.environ
        cls.save_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        """Restore environment"""
        os.chdir(cls.save_cwd)
        os.environ = cls.save_env

    def setUp(self):
        """Before every test"""
        logging.debug("\n%s", "-" * 70)

    def check_command(self, cmd, exit_code=0, working_dir=None):
        """Run shell command and check status.
        WARNING: Working directory by default will be in unit/common."""
        logging.debug("Running: %s", cmd)
        commands = shlex.split(cmd)
        with subprocess.Popen(
            commands,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_dir,
        ) as process:
            stdout, stderr = process.communicate()
            self.assertEqual(
                process.returncode,
                exit_code,
                "\n"
                + "\n".join(
                    [
                        f"command: {cmd}",
                        f"stdout: {stdout.decode('utf-8')}",
                        f"stderr: {stderr.decode('utf-8')}",
                    ]
                ),
            )
            return (
                f"stdout: {stdout.decode('utf-8')}",
                f"stderr: {stderr.decode('utf-8')}",
            )

    def grep_file(self, filename, regex):
        """Grep given filename.
        WARNING: Working directory will be in unit/common."""
        pattern = re.compile(regex)
        logging.debug("RegEx = r'%s'", regex)
        with open(filename, "r", encoding="utf-8") as fileobj:
            for line in fileobj:
                if pattern.search(line):
                    logging.debug(line)
                    return line
        self.fail(f"Could not find r'{regex}' in '{filename}'")
        return ""
