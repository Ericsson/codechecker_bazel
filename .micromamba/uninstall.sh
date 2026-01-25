THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

MICROMAMBA=".micromamba"
if [[ "$(basename $THIS_DIR)" == "$MICROMAMBA" ]]; then
    PROCESSES="bazel java python3 CodeChecke"
    echo "Killing: $PROCESSES"
    timeout 10s killall --quiet --wait $PROCESSES
    killall --quiet -SIGKILL $PROCESSES

    echo "Removing micromamba from: $THIS_DIR"
    rm -rf $THIS_DIR/bin
    chmod -R +w $THIS_DIR/micromamba
    rm -rf $THIS_DIR/micromamba

    # for directory in $THIS_DIR/*/; do
    #     if [[ -d "$directory" ]]; then
    #         echo "Removing: $directory"
    #         chmod -R +w $directory
    #         rm -rf $directory
    #     fi
    # done
    echo "Please exit current shell session"
else
    echo "Error: wring location $THIS_DIR"
    echo "       $MICROMAMBA is not there"
    exit 1
fi
