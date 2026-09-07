# CI Docker Images

These Dockerfiles allows you to test the rules set in a sandbox environment.
Each Dockerfile has its own folder with the name of the distribution its based on.
The `entrypoint.sh` script stores the commands for running tests, and wil be executed when running the images with `docker run`.

## Quick Start

```bash
# Build
docker build -t rules-codechecker-ubuntu -f .ci/docker/ubuntu/Dockerfile .ci/docker
docker build -t rules-codechecker-rhel9  -f .ci/docker/rhel9/Dockerfile .ci/docker
```
If you encounter network related issues try passing the flag: `--network=host`.

# Run tests against the project (mount project root to /workspace)

### Note:
To set the bazel version either create a `.bazelversion` file in the root of the project, or define the version with the `-e BAZEL_VERSION=x.x.x` parameter.
Bazel version defaults to `7.7.0`.

```bash
docker run --rm \
    -v "$(pwd):/workspace" \
    rules-codechecker-ubuntu

docker run --rm \
    -v "$(pwd):/workspace" \
    rules-codechecker-rhel9
```
If you encounter network related issues try passing the flag: `--network=host`, as shown below.

```
docker run --rm \
    --network=host \
    -v "$(pwd):/workspace" \
    rules-codechecker-ubuntu
```

Example for setting the bazel version using docker run parameters.
```
docker run --rm \
    -e BAZEL_VERSION=7.7.0 \
    -v "$(pwd):/workspace" \
    rules-codechecker-ubuntu
```

### To remove artifacts created by docker run:

```
docker -rmi rules-codechecker-ubuntu
docker -rmi rules-codechecker-rhel9
```
