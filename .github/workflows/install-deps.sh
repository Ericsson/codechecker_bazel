#!/bin/bash

# NOTE: clang-18 is the latest version available from the package manager at the
# time of writing this test. Since we're not testing clang here, but rather how
# the bazel rules work, it is _usually_ not important to regularly update clang
# to the newest available. In fact, CodeChecker itself tests with clang-14 so
# their tests don't need to be updated at every clang release, which requires
# setting up a ppa. See here:
# https://github.com/Ericsson/codechecker/blob/master/.github/workflows/install-deps.sh
# Same applies for g++, clang-tools, etc.

sudo apt-get update --quiet

sudo apt-get install --no-install-recommends \
  g++-14 \
  clang-18 \
  clang-tools-18 \
  clang-tidy-18 \
  cppcheck

# Rename clang-18 to clang, etc.

sudo update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-18 9999
sudo update-alternatives --install /usr/bin/clang-extdef-mapping \
  clang-extdef-mapping /usr/bin/clang-extdef-mapping-18 9999
sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-18 9999
sudo update-alternatives --install /usr/bin/clang-tidy clang-tidy /usr/bin/clang-tidy-18 9999
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-14 9999

# Source: https://fbinfer.com/docs/getting-started
VERSION=1.1.0; \
curl -sSL "https://github.com/facebook/infer/releases/download/v$VERSION/infer-linux64-v$VERSION.tar.xz" \
| sudo tar -C /opt -xJ && \
sudo ln -s "/opt/infer-linux64-v$VERSION/bin/infer" /usr/local/bin/infer
