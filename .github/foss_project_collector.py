# Copyright 2023 Ericsson AB
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

import os
import json
import sys
import glob


IGNORED_FOLDER_LIST = [
    "templates",
    "__pycache__",
    ".pytest_cache",
]

def main():
    projects_dir = os.getenv("PROJECTS_DIR")
    if not projects_dir:
        print("[ERROR] PROJECTS_DIR not set!", file=sys.stderr)
        sys.exit(1)

    project_list = []

    for project_folder in glob.glob(os.path.join(projects_dir, "*/")):
        project_name = os.path.basename(os.path.normpath(project_folder))

        if project_name not in IGNORED_FOLDER_LIST:
            project_list.append(
                {"name": project_name, "folder": project_folder}
            )

    final_matrix_json = json.dumps(project_list)

    print(f"matrix_json={final_matrix_json}")


if __name__ == "__main__":
    main()
