THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

MICROMAMBA=".ci/micromamba"
if [[ "$(basename $THIS_DIR)" == "$MICROMAMBA" ]]; then
    PROCESSES="bazel java python3 CodeChecker"
    echo "Killing: $PROCESSES"
    timeout 10s killall --quiet --wait $PROCESSES
    killall --quiet -SIGKILL $PROCESSES

    echo "Removing micromamba from: $THIS_DIR"
    rm -rf $THIS_DIR/bin
    chmod -R +w $THIS_DIR/micromamba
    rm -rf $THIS_DIR/micromamba

    echo "Please exit current shell session"
else
    echo "Error: wring location $THIS_DIR"
    echo "       $MICROMAMBA is not there"
    exit 1
fi
