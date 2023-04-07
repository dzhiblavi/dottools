source "${HOME}/.bash_completion.d/common/loader.sh"

_dd_load 'common/options'
_dd_load 'common/scp_completer'

#
# Puts available dots configuration names into the specified variable as array
# arg0 : variable array to store config names
#
function _dd_dots_get_configs() {
    local out_var="$1"
    local configs_root="$(dirname ${DOTTOOLS_CFG_PATH:-'~/dotfiles/config/'})"

    if ! [ -d "${configs_root}" ]; then
        eval "${out_var}=''"
        return 0
    fi

    for path in "${configs_root}"/*; do
        eval "${out_var}+=(\"${path}\")"
    done
}

#
# Performs argument completion for dots utility
#
function _dd_dots_complete() {
    local reply=()
    local cur
    local prev
    local words
    local cword
    _get_comp_words_by_ref -n : cur prev words cword

    case "${prev}" in
        '-c'|'--config-file') _dd_dots_get_configs reply ;;
        '-r'|'--root') reply+=("${DOTFILES_ROOT:-'~/dottools'}") ;;
        *) {
            reply+=(                   \
                "--help"               \
                "bashrc"               \
                "dotfiles"             \
                "diff"                 \
                "all"                  \
                "--dry-run"            \
                "-c" "--config-file"   \
                "-r" "--root"          \
            )
        } ;;
    esac

    _dd_complete_by_prefix "${cur}" "${reply[@]}"
}

complete -F _dd_dots_complete dots

