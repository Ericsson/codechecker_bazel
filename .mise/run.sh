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
    eval "$(~/.local/bin/mise activate --shims bash)"
fi
mise trust --quiet
mise version
export MISE_CONDA_CONCURRENCY=1
mise install || mise install
mise reshim

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    mise run ${@}
else
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

    # CLANG_PATH="$HOME/.local/share/mise/installs/conda-clang/latest"
    # TOOLS_PATH="$HOME/.local/share/mise/installs/conda-clang-tools/latest"
    # echo "Creating symlinks for clang tools"
    # echo "clang: $CLANG_PATH"
    # echo "tools: $TOOLS_PATH"
    # if [[ -n "$CLANG_PATH" && -n "$TOOLS_PATH" && "$CLANG_PATH" != "$TOOLS_PATH" ]]; then
    #     for file in $TOOLS_PATH/*; do
    #         filename=$(basename $file)
    #         if [ ! -L $CLANG_PATH/$filename ]; then
    #             # echo "$file -> $CLANG_PATH/$filename"
    #             ln -snf $file $CLANG_PATH/$filename
    #         fi
    #     done
    #     mise reshim
    # fi
fi
