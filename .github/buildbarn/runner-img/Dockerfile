FROM ubuntu:22.04

# Set noninteractive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Update and install essential tools
RUN apt update && apt install -y \
    build-essential \
    clang \
    clang-tidy \
    clang-tools \
    libc6-dev \
    lld \
    gcc-11 \
    g++-11 \
    cmake \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    unzip && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install \
    /usr/bin/clang-extdef-mapping \
    clang-extdef-mapping \
    /usr/bin/clang-extdef-mapping-$(clang --version | head -n 1 | \
    sed -E 's/.*version ([0-9]+)\..*/\1/') \
    100

# Setup python virtual enviroments
RUN python3 -m venv /venv

# Set py vevn as always active
ENV VIRTUAL_ENV=/venv
ENV PATH=/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/snap/bin

# Install CodeChecker and any other dependencies
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir codechecker

RUN ln -s /venv/bin/CodeChecker /usr/bin/CodeChecker

WORKDIR /worker

