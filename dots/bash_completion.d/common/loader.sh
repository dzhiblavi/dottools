#
# Load completion script by its path in .bash_completion.d
#
function _dd_load() {
    local name="$1"
    . "${HOME}/.bash_completion.d/${name}.sh"
}

