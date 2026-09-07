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

# Usage:
#   docker build -t rules-codechecker-ubuntu .ci/docker/ubuntu/
#   docker run --rm -v "$(pwd):/workspace" rules-codechecker-ubuntu

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

RUN apt-get update --quiet \
    && apt-get install --no-install-recommends -y \
        clang \
        clang-tools \
        clang-tidy \
        python3 \
        python3-pip \
        python3-venv \
        wget \
        git \
        gcc \
        g++ \
        ca-certificates \
        rsync \
    && rm -rf /var/lib/apt/lists/*

# The versioned binary (e.g. clang-extdef-mapping-18) is installed by
# clang-tools; we expose it under the unversioned name so bazel rules find it.
RUN CLANG_MAJOR=$(clang --version | head -n1 \
    | sed -E 's/.*version ([0-9]+)\..*/\1/') \
    && update-alternatives --install \
    /usr/bin/clang-extdef-mapping \
    clang-extdef-mapping \
    /usr/bin/clang-extdef-mapping-${CLANG_MAJOR} \
    100

# We install bazelisk as the `bazel` binary; the actual Bazel version is
# controlled at runtime via the .bazelversion file in the project root.
ARG BAZELISK_VERSION=1.26.0
RUN wget -q \
    "https://github.com/bazelbuild/bazelisk/releases/download/v${BAZELISK_VERSION}/bazelisk-linux-amd64" \
    -O /usr/local/bin/bazel \
    && chmod +x /usr/local/bin/bazel

# pip install inside a venv to avoid the "externally-managed" error on 24.04.
ENV VIRTUAL_ENV=/opt/codechecker-venv
RUN python3 -m venv "$VIRTUAL_ENV" \
    && "$VIRTUAL_ENV/bin/pip" install --no-cache-dir codechecker pytest pylint==3.0.0

# Put the venv binaries on PATH so `CodeChecker` is found by bazel & tests
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Bazel's hermetic Python toolchain refuses to run as root 
# Create a dedicated user and run as them.
RUN useradd -m -s /bin/bash ci

# The project root is expected to be mounted here at runtime:
#   docker run --rm -v "$(pwd):/workspace" ...
RUN mkdir -p /workspace \
    && chown ci:ci /workspace
WORKDIR /workspace

# Give the ci user a writable Bazel cache directory.
RUN mkdir -p /home/ci/.cache/bazel \
    && chown -R ci:ci /home/ci/.cache

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER ci
ENTRYPOINT ["/entrypoint.sh"]
