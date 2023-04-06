#!/usr/bin/env bash

function vw() {
    local WHAT="${1:-.}"
    if [[ -d "$WHAT" ]]; then
        ls "$WHAT"
    elif [[ -f "$WHAT" ]]; then
        cat "$WHAT"
    else
        print_error "Invalid argument for view: neither file nor directory: $WHAT"
    fi
}

function convert() {
    date -d "@$1"
}

function watcha() {
    CMD="$1"
    shift
    watch -n 0.1 --color "$(alias "$CMD" | cut -d\' -f2) $*"
}

function contains_element() {
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}

function update_config() {
    local FILE="$1"
    if ! [[ -f "$FILE" ]]; then
        touch "$FILE"
    fi
    local CONTENT="$2"
    printf '%s' "$CONTENT" > "$FILE"
}

