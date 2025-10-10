#!/usr/bin/env bash
set -eu

worker_fuse="worker-fuse-ubuntu22-04"
worker_hardlinking="worker-hardlinking-ubuntu22-04"
fuse_dir_to_unmount="volumes/${worker_fuse}/build"
sudo -v

cleanup() {
    EXIT_STATUS=$?
    local -
    set -x

    sudo fusermount -u "$fuse_dir_to_unmount" || true
    exit "$EXIT_STATUS"
}

cleanup
