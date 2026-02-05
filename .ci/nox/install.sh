#!/bin/bash

# ENFORCE SOURCING
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Usage: source setup_mamba.sh"
    exit 1
fi

INSTALL_DIR="$(pwd)/bin"
export MAMBA_ROOT_PREFIX="$(pwd)/micromamba"
export MAMBA_EXE="$INSTALL_DIR/micromamba"

# DOWNLOAD IF MISSING
if [ ! -f "$MAMBA_EXE" ]; then
    echo "Downloading micromamba to $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C "$(pwd)" bin/micromamba
fi

export PATH="$INSTALL_DIR:$PATH"
eval "$($MAMBA_EXE shell hook --shell bash --root-prefix $MAMBA_ROOT_PREFIX)"
