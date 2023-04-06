#!/usr/bin/env bash

ESC="\033"

CLR_NC="${ESC}[0m"
CLR_BLACK="${ESC}[0;30m"
CLR_RED="${ESC}[0;31m"
CLR_GREEN="${ESC}[0;32m"
CLR_YELLOW="${ESC}[0;33m"
CLR_BLUE="${ESC}[0;34m"
CLR_MAGENTA="${ESC}[0;35m"
CLR_CYAN="${ESC}[0;36m"
CLR_LIGHT_GRAY="${ESC}[0;37m"
CLR_GRAY="${ESC}[0;90m"
CLR_LIGHT_RED="${ESC}[0;91m"
CLR_LIGHT_GREEN="${ESC}[0;92m"
CLR_LIGHT_YELLOW="${ESC}[0;93m"
CLR_LIGHT_BLUE="${ESC}[0;94m"
CLR_LIGHT_MAGENTA="${ESC}[0;95m"
CLR_LIGHT_CYAN="${ESC}[0;96m"
CLR_WHITE="${ESC}[0;97m"

BG_BLACK="${ESC}[40m"
BG_RED="${ESC}[41m"
BG_GREEN="${ESC}[42m"
BG_YELLOW="${ESC}[43m"
BG_BLUE="${ESC}[44m"
BG_MAGENTA="${ESC}[45m"
BG_CYAN="${ESC}[46m"
BG_LIGHT_GRAY="${ESC}[47m"
BG_GRAY="${ESC}[100"
BG_LIGHT_RED="${ESC}[101"
BG_LIGHT_GREEN="${ESC}[102m"
BG_LIGHT_YELLOW="${ESC}[103m"
BG_LIGHT_BLUE="${ESC}[104m"
BG_LIGHT_MAGENTA="${ESC}[105m"
BG_LIGHT_CYAN="${ESC}[106m"
BG_WHITE="${ESC}[107m"

MD_BOLD="${ESC}[1m"
MD_FAI="${ESC}[2m"
MD_ITA="${ESC}[3m"
MD_UND="${ESC}[4m"

function print_clr() {
    local CLR="$1"
    local CONTENT="$2"
    COLOR_OUT="${CLR}${CONTENT}${CLR_NC}"
}

function print_info() {
    >&2 echo -e "$(date):[${CLR_GREEN}INFO${CLR_NC}]\t$*"
    return 0
}

function print_warn() {
    >&2 echo -e "$(date):[${CLR_YELLOW}WARN${CLR_NC}]\t$*"
    return 0
}

function print_error() {
    >&2 echo -e "$(date):[${CLR_RED}ERROR${CLR_NC}]\t$*"
    return 1
}

