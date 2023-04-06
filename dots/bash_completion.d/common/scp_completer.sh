#
# Use scp completer (_scp) to complete arguments.
# Useful for paths that could be remote (e.g. host:~/dir/file)
# arg0 : word to complete
#
function _dd_complete_scp() {
    [[ $(type -t _scp) == function ]] || _completion_loader scp
    _scp "scp" "$1" ""
}

