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
#   docker build -t rules-codechecker-rhel9 .ci/docker/rhel9/
#   docker run --rm -v "$(pwd):/workspace" rules-codechecker-rhel9

FROM redhat/ubi9:latest

RUN dnf update -y \
    && dnf install -y \
    llvm-toolset \
    clang-tools-extra \
    wget \
    git \
    python3 \
    python3-pip \
    gcc \
    g++ \
    scl-utils \
    rsync \
    && dnf clean all

ARG BAZELISK_VERSION=1.26.0
RUN wget -q \
    "https://github.com/bazelbuild/bazelisk/releases/download/v${BAZELISK_VERSION}/bazelisk-linux-amd64" \
    -O /usr/local/bin/bazel \
    && chmod +x /usr/local/bin/bazel

RUN pip3 install --no-cache-dir codechecker pytest pylint==3.0.0

# Required by Bazel's hermetic Python toolchain (rules_python refuses root).
RUN useradd -m -s /bin/bash ci

# The project root is expected to be mounted here at runtime:
#   docker run --rm -v "$(pwd):/workspace" ...
RUN mkdir -p /workspace \
    && chown ci:ci /workspace
WORKDIR /workspace

RUN mkdir -p /home/ci/.cache/bazel \
    && chown -R ci:ci /home/ci/.cache

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER ci
ENTRYPOINT ["/entrypoint.sh"]
