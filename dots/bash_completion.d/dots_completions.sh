source "${HOME}/.bash_completion.d/common/loader.sh"

_dd_load 'common/options'
_dd_load 'common/scp_completer'

#
# Puts available dots configuration names into the specified variable as array
# arg0 : variable array to store config names
#
function _dd_dots_get_types() {
    local out_var="$1"
    local dotfiles_root="${DOTFILES_ROOT:-'~/dotfiles'}"

    if ! [ -d "${dotfiles_root}" ]; then
        eval "${out_var}=''"
        return 0
    fi

    for path in "${dotfiles_root}"/configs/*; do
        file="$(basename "${path}")"
        type="${file::-5}"
        eval "${out_var}+=(\"${type}\")"
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
        '-t'|'--type') _dd_dots_get_types reply ;;
        '--dotfiles-root'|'-r') reply+=("${DOTFILES_ROOT:-'~/dotfiles'}") ;;
        'sync') reply+=("--help" "-d" "--destination") ;;
        '-d'|'--destination') _dd_complete_scp ;;
        *) {
            reply+=(                   \
                "--help"               \
                "bashrc"               \
                "dotfiles"             \
                "sync"                 \
                "diff"                 \
                "all"                  \
                "--dry-run"            \
                "-t" "--type"          \
                "-r" "--dotfiles-root" \
            )
        } ;;
    esac

    _dd_complete_by_prefix "${cur}" "${reply[@]}"
}

complete -F _dd_dots_complete dots

