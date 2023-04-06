#
# Filters completions by prefix
# arg0   : prefix
# arg1.. : completions
#
function _dd_complete_by_prefix() {
    local prefix="$1"
    shift
    for reply in "$@"; do
        [[ $reply == ${prefix}* ]] && COMPREPLY+=("$reply")
    done
}
