# { Part of bashrc file [ scripts/common/fsdb.sh ]

function dotsdb_put() {
    default_db_path="${HOME}/.dots_db_store"
    db_path="${DOTFILES_DB_FILE:-${default_db_path}}"

    local key_enc="$(echo $1 | base64)"
    local val_enc="$(echo $2 | base64)"

    echo "${key_enc},${val_enc}" >> "${db_path}"
}

function dotsdb_get() {
    default_db_path="${HOME}/.dots_db_store"
    db_path="${DOTFILES_DB_FILE:-${default_db_path}}"

    local key_enc="$(echo $1 | base64)"
    local val_enc="$(grep "^${key_enc}," "${db_path}" | awk -F',' '{print $2}' | tail -n 1)"

    [[ -z "${val_enc}" ]] && {
        echo ""
    } || {
        local val="$(echo ${val_enc} | base64 -d)"
        echo "${val}"
    }
}

# } Part of bashrc file [ scripts/common/fsdb.sh ]
