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
import sys
import shutil
import subprocess

FOSS_BASE_DIR = "./foss"

def main():
    """
    Finds all open source project and calls the tests on each of them
    """
    if not os.path.isdir(FOSS_BASE_DIR):
        print(f"Error: The directory '{FOSS_BASE_DIR}' does not exist.")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_projects()
        sys.exit(0)

    print(f"Starting in '{FOSS_BASE_DIR}' ...")
    print("-----------------------------------------------------------------")

    if shutil.which("CodeChecker") is None:
        print("CodeChecker not found! Terminating...")
        print("----------------------------------------------------------\
              -------")
        sys.exit(1)

    try:
        for project_name in os.listdir(FOSS_BASE_DIR):
            project_dir = os.path.join(FOSS_BASE_DIR, project_name)

            if not os.path.isdir(project_dir):
                continue

            if project_name == "templates":
                continue

            process_project(project_dir, project_name)

    except OSError as e:
        print(f"An error occurred while processing directories: {e}")
        sys.exit(1)

    print("\n-----------------------------------------------------------------")
    print("Done.")

def clean_projects():
    """
    Finds and removes 'test-proj' directories and log files
    """
    print("Starting cleanup process...")
    for root, dirs, files in os.walk(FOSS_BASE_DIR):
        depth = root.count(os.sep) - FOSS_BASE_DIR.count(os.sep)
        if depth == 1 and "test-proj" in dirs:
            test_proj_path = os.path.join(root, "test-proj")
            print(f"Removing directory: {test_proj_path}")
            shutil.rmtree(test_proj_path)
        if "codechecker.log" in files:
            log_pth = os.path.join(root, "codechecker.log")
            print(log_pth)
            os.remove(log_pth)
        if "code_checker.log" in files:
            log_pth = os.path.join(root, "code_checker.log")
            print(log_pth)
            os.remove(log_pth)

def process_project(project_dir, project_name):
    """
    Handles the initializing and testing process for a single project.
    """
    print(f"\nProcessing project: {project_name} ({project_dir})")
    print("-----------------------------------------------------------------")

    test_proj_dir = os.path.join(project_dir, "test-proj")
    init_script_path = os.path.join(project_dir, "init.sh")

    if not os.path.isdir(test_proj_dir):
        print("  Running ./init.sh...")
        
        if not os.path.isfile(init_script_path):
            print(f"  Warning: ./init.sh not found in {project_name}. \
                  Skipping.")
            print("---------------------------------------------------------\
                  --------")
            return
        
        if not os.access(init_script_path, os.X_OK):
            print(f"  Warning: ./init.sh found in {project_name} \
                  but it is not executable.")
            print("  Please run 'chmod +x init.sh' inside the project \
                  directory and try again.")
            print("-------------------------------------------------------\
                  ----------")
            return
            
        try:
            subprocess.run(
                ["./init.sh"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError:
            print(f"  Warning: ./init.sh failed for {project_name}. Skipping.")
            print("------------------------------------------------------\
                  -----------")
            return
    else:
        print(f"test-proj already exists. Skipping init.sh for {project_name}")

    if os.path.isdir(test_proj_dir):
        print("  Running bazel build :codechecker_test...")
        try:
            tee_proc = subprocess.Popen(["tee", "../codechecker.log"],
                            stdin=subprocess.PIPE, cwd=test_proj_dir, text=True)

            subprocess.run(
                ["bazel", "build", ":codechecker_test"],
                cwd=test_proj_dir,
                stdout=tee_proc.stdin,
                stderr=tee_proc.stdin,
                text=True,
                check=True
            )

            tee_proc.stdin.close()
            tee_proc.wait()

        except subprocess.CalledProcessError:
            print(f"  Error: 'bazel build :codechecker_test' failed for \
                  {project_name}. Check logs above or in \
                  {project_dir}/codechecker.log.")

        print("  Running bazel build :code_checker_test...")
        try:
            tee_proc = subprocess.Popen(["tee", "../code_checker.log"],
                            stdin=subprocess.PIPE, cwd=test_proj_dir, text=True)
            
            subprocess.run(
                ["bazel", "build", ":code_checker_test"],
                cwd=test_proj_dir,
                stdout=tee_proc.stdin,
                stderr=tee_proc.stdin,
                text=True,
                check=True
            )

            tee_proc.stdin.close()
            tee_proc.wait()
        except subprocess.CalledProcessError:
            print(f"  Error: 'bazel build :code_checker_test' failed for \
                  {project_name}. Check logs above or in \
                  {project_dir}/code_checker.log.")
    else:
        print(f"  Error: 'test-proj' directory not found in {project_name}. \
              Skipping Bazel builds.")

    print("-----------------------------------------------------------------")
    print(f"Finished processing project: {project_name}")


if __name__ == "__main__":
    main()
