# FIXME: We need MISE_GITHUB_TOKEN to download from GitHub
#        since URLs are not supported in lock files for pipx
#        See https://mise.jdx.dev/dev-tools/mise-lock.html#backend-support
# export MISE_GITHUB_TOKEN="XxXx..."

# Make sure we source the script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script must be 'sourced':"
    echo "       source ${0}"
    exit 1
fi

# Install mise if not installed
if [ ! -f ~/.local/bin/mise ]; then
    curl https://mise.run | sh
fi

# Activate mise if not activated
if ! command -v mise >/dev/null 2>&1; then
    eval "$(~/.local/bin/mise activate --shims bash)"
fi

# Install default tools
mise trust --quiet
mise version
export MISE_CONDA_CONCURRENCY=1
mise install || mise install
mise reshim

# NOTE: The following hack is needed to have clang and some tools
#       to be in the same location (neer to clang)
clang_tools="diagtool clang-extdef-mapping"
clang_bin_dir=$(mise which clang | xargs dirname)
if [[ -n "$clang_bin_dir" ]]; then
    for tool in $clang_tools; do
        tool_path=$(mise which $tool)
        if [[ -n "$tool_path" && ! -L "$clang_bin_dir/$tool" ]]; then
            echo "Creating symlink for $tool"
            ln -snf $tool_path $clang_bin_dir/$tool
        fi
    done
    mise reshim
else
    echo "ERROR: Could not find clang bin dir"
fi
