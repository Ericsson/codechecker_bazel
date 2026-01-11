#!/usr/bin/env bash

# FIXME: We need MISE_GITHUB_TOKEN to download from GitHub
#        since URLs are not supported in lock files for pipx
#        See https://mise.jdx.dev/dev-tools/mise-lock.html#backend-support
# export MISE_GITHUB_TOKEN="XxXx..."

if ! command -v mise >/dev/null 2>&1; then
    echo "Install Mise:"
    curl https://mise.run | sh
    eval "$(~/.local/bin/mise activate bash)"
fi
mise trust
mise version
mise install

mise ${@:- test}
