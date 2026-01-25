# Make sure we source the script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script must be 'sourced':"
    echo "       source ${0}"
    exit 1
fi

# Parse arguments
unset VERBOSE
MAMBA_VERBOSITY="--quiet"
args=()
for arg in "$@"; do
    if [[ "$arg" == "-v" ]]; then
        VERBOSE=1
    elif [[ "$arg" == "-vv" ]]; then
        VERBOSE=2
        MAMBA_VERBOSITY=""
    else
        args+=("${arg}")
    fi
done
set -- "${args[@]}"
unset args

# Logging function
function log() {
    [[ -n "$VERBOSE" ]] && echo "[micromamba] $@"
}

# Logging function
function info() {
    echo "[micromamba] $@"
}

# Get the environment name
log "Arguments: \"$@\""
ENV_NAME="${1:-dev}"
log "Environment: $ENV_NAME"

# Get the location of this script
THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
log "Location: $THIS_DIR"

# Check if we have environment file
if [ ! -f $THIS_DIR/$ENV_NAME.yaml ]; then
    info "ERROR: No environment file found: $THIS_DIR/$ENV_NAME.yaml"
    return 1
fi

# Install micromamba if not installed
# See https://mamba.readthedocs.io
if [ ! -f $THIS_DIR/bin/micromamba ]; then
    info "Installing to $THIS_DIR/bin ..."
    pushd $THIS_DIR > /dev/null
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba
    popd > /dev/null
else
    info "Using: $(ls $THIS_DIR/bin/micromamba)"
fi

# Initialize shell with micromamba
export MAMBA_EXE="$THIS_DIR/bin/micromamba";
export MAMBA_ROOT_PREFIX="$THIS_DIR/micromamba";
eval "$($MAMBA_EXE shell hook --shell bash --root-prefix $MAMBA_ROOT_PREFIX)"
log "Micromamba:"
log "MAMBA_EXE=$MAMBA_EXE"
log "MAMBA_ROOT_PREFIX=$MAMBA_ROOT_PREFIX"
if [[ "$VERBOSE" -ge 2 ]]; then
    micromamba info
fi

# Create environment
info "Creating environment [$ENV_NAME]..."
micromamba create --file $THIS_DIR/$ENV_NAME.yaml --name $ENV_NAME --yes $MAMBA_VERBOSITY
# micromamba config set env_prompt "[{name}] "
micromamba activate $ENV_NAME

# # Create environment
# info "Creating environment [$ENV_NAME]..."
# micromamba create --file $THIS_DIR/$ENV_NAME.yaml --prefix $THIS_DIR/$ENV_NAME --yes $MAMBA_VERBOSITY
# micromamba config set env_prompt "[{name}] "
# micromamba activate $THIS_DIR/$ENV_NAME

# Print out tools information
if [[ -n "$VERBOSE" ]]; then
    log "Tools:"
    which python3
    which bazel
    which CodeChecker
    which pytest
    which pylint
    which pycodestyle
    which buildifier
    which clang
    which clang-tidy
    which diagtool
    which clang-extdef-mapping
fi

# Unset variables
unset ENV_NAME
unset THIS_DIR
unset MAMBA_VERBOSITY
info "To exit session run: micromamba deactivate"
