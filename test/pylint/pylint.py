# Copyright 2026 Ericsson AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Run pylint on the Python files of the repository.

Pylint comes from PyPI, see MODULE.bazel, and runs in the repository root.
The root is the directory of the workspace file, given as the first argument.
The remaining arguments are passed to pylint.
"""

import os
import sys

# pylint: disable=import-self
from pylint import lint
from pylint import version


def main():
    """Run pylint with the configuration of this package"""
    if len(sys.argv) < 2:
        print("Usage: pylint.py <workspace file> [pylint options]")
        sys.exit(1)
    workspace_file = sys.argv[1]
    if not os.path.exists(workspace_file):
        print(f"Workspace file is not in the runfiles: {workspace_file}")
        sys.exit(1)
    root = os.path.dirname(os.path.realpath(workspace_file))
    args = sys.argv[2:]
    print(f"Running pylint {version} from {lint.__file__}")
    print(f"Repository: {root}")
    print(f"Arguments: {args}")
    os.chdir(root)
    lint.Run(args)


if __name__ == "__main__":
    main()
