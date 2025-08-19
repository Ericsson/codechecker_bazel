## Testing on open source projects

## Add a new open source project:

1. Create a folder in the foss folder with the name of the project.
2. The folder should contain:
    - init.sh

3. The init.sh script should:
  - Clone the test project into a folder named `test-proj`.
  - To ensure the project doesn't change over time, check out a specific tag or commit instead of a branch!
  - Copy the .bazelversion file from the templates directory into the test-proj directory.
  - Append the WORKSPACE.template file to the WORKSPACE file of the project.
  - Append the codechecker rules to the BUILD file of the project.
    - There can be only two targets, codechecker_test and code_checker_test
