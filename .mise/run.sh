#!/usr/bin/env bash

# FIXME: We need MISE_GITHUB_TOKEN to download from GitHub
#        since URLs are not supported in lock files for pipx
#        See https://mise.jdx.dev/dev-tools/mise-lock.html#backend-support
# export MISE_GITHUB_TOKEN="XxXx..."

if [ ! -f ~/.local/bin/mise ]; then
    # Install mise:
    curl https://mise.run | sh
fi
if ! command -v mise >/dev/null 2>&1; then
    # Activate mise:
    eval "$(~/.local/bin/mise activate bash)"
fi
mise trust
mise version
mise install

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    mise run ${@}
fi
