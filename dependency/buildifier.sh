#!/bin/bash
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: This script must be run using 'source'"
    echo "Usage: source $0 [clean|force]"
    exit 1
fi

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TARGET_DIR="$THIS_DIR/bin"
TARGET_PATH="$TARGET_DIR/buildifier"

VERSION="v8.5.1"
URL="https://github.com/bazelbuild/buildtools/releases/download/${VERSION}/buildifier-linux-amd64"

case "$1" in
    clean)
        echo "Cleaning Buildifier installation..."
        rm -f "$TARGET_PATH"
        unalias buildifier 2>/dev/null
        unset BUILDIFIER_EXE
        return 0
        ;;
    force)
        echo "Force flag detected. Removing existing binary..."
        rm -f "$TARGET_PATH"
        ;;
    *)
        # Default behavior
        ;;
esac

if [ ! -f "$TARGET_PATH" ]; then
    echo "Installing Buildifier to $TARGET_DIR ..."
    mkdir -p "$TARGET_DIR"
    if curl -Ls "$URL" -o "$TARGET_PATH"; then
        chmod +x "$TARGET_PATH"
        echo "Buildifier installed successfully."
    else
        echo "Error: Failed to download Buildifier."
        return 1
    fi
else
    echo "Buildifier already installed"
fi

export BUILDIFIER_EXE="$TARGET_PATH"
alias buildifier='$BUILDIFIER_EXE'
