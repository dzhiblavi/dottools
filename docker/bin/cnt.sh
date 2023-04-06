#!/bin/bash -i
set -e

br_import 'print'

# Kinda check for GPU presence
function has_gpu() {
    command -v nvidia-smi &> /dev/null \
    || return 1                        \
    && {
        nvidia-smi 2>&1 >/dev/null
    }
}

function docker_get_container() {
    CONTAINER=$(docker container ls "$@" | grep "${IMAGE_NAME}" | awk '{ print $1 }')
}

function check_running_container() {
    docker_get_container
    [[ -n "${CONTAINER}" ]] && return 0 || return 1
}

function check_any_container() {
    docker_get_container --all
    [[ -n "${CONTAINER}" ]] && return 0 || return 1
}

function restart_container() {
    check_running_container \
        && { print_warn "Container is already running (id=${CONTAINER})."; return 0; }

    check_any_container \
        || { print_error "Cannot find a container to restart"; return 1; }

    docker container restart "${CONTAINER}" >/dev/null                      \
        && print_info "Successfully restarted ${CONTAINER} (${IMAGE_NAME})" \
        || print_error "Failed to restart ${CONTAINER}"
}

function start_container() {
    check_running_container \
        && { print_warn "Container is already started (id=${CONTAINER})"; return 0; }

    check_any_container && {
        print_warn "Found suitable stopped container (id=${CONTAINER}), restarting..."
        restart_container && return $?
    }

    local mnt_local="${HOME}/${DOCKER_MNT_DIR_NAME}"
    local mnt_home="/home/${USER}/${DOCKER_MNT_DIR_NAME}"
    local mnt_root="/${DOCKER_MNT_DIR_NAME}"

    has_gpu && { local gpu_options="--gpus all"; } || { local gpu_options=""; }

    docker run >/dev/null                                               \
        --net=host                                                      \
        --mount type=bind,source="${mnt_local}",target="${mnt_root}"    \
        --mount type=bind,source="${mnt_local}",target="${mnt_home}"    \
        --security-opt seccomp=docker/seccomp.json                      \
        --cap-add SYS_ADMIN                                             \
        --privileged -dit ${gpu_options}                                \
        $@                                                              \
        "${IMAGE_NAME}"                                                 \
        && print_info "Started container."                              \
        || print_error "Failed to start container!"
}

function attach_to_container() {
    check_running_container || {
        print_warn "Container is not started. Trying to restart stopped container..."
        restart_container
    } || {
        print_warn "Container is not started. Trying to start container..."
        start_container
    } && {
        check_running_container 
        docker exec -it "${CONTAINER}" $@
    }
}

function stop_container() {
    check_running_container || { print_warn "Container is not started."; return 0; }

    docker container stop "${CONTAINER}" >/dev/null          \
        && print_info "Stopped container (id=${CONTAINER})." \
        || print_error "Failed to stop container (id=${CONTAINER})!"
}

function delete_container() {
    check_running_container && {
        print_warn "Stopping container... (id=${CONTAINER})"
        stop_container || return $?
    }

    check_any_container || { print_error "Stopped container not found."; return 1; }

    docker container rm "${CONTAINER}" >/dev/null                     \
        && print_info "Container (id=${CONTAINER}) has been removed." \
        || print_error "Failed to remove container (id=${CONTAINER})"
}

function show_containers_status() {
    docker container ls --all --filter status=running | while read line; do
        print_info "$line"
    done 
    docker container ls --all --filter status=exited | while read line; do
        print_warn "$line"
    done 
}

function containers_main() {
    [[ $# -eq 0 ]] && { show_containers_status; print_info "${CONTAINERS_USAGE}"; return 1; }

    IMAGES=()
    while [[ -n "$1" ]]; do
        case "$1" in
            -a|--attach) {
                ATTACH=1
            } ;;
            '-?'|--status) {
                show_containers_status
            } ;;
            -s|--stop) {
                STOP=1
            } ;;
            --start) {
                RUN=1
            } ;;
            -r|--restart) {
                RESTART=1                
            } ;;
            --delete) {
                DELETE=1
            } ;;
            --) {
                shift
                break
            } ;;
            *) {
                IMG="$1"
                IMAGES+=("${IMG}")
            } ;;
        esac
        shift
    done

    for IMAGE_NAME in "${IMAGES[@]}"; do
        print_info "Image: ${IMAGE_NAME}"
        [[ ${RUN-0}         -eq 1 ]] && start_container "$@"
        [[ ${RESTART-0}     -eq 1 ]] && restart_container "$@"
        [[ ${ATTACH-0}      -eq 1 ]] && attach_to_container /bin/bash "$@"
        [[ ${STOP-0}        -eq 1 ]] && stop_container "$@"
        [[ ${DELETE-0}      -eq 1 ]] && delete_container "$@"
    done
}

CONTAINERS_USAGE="[-a|--attach -r|--restart -?|--status -s|--stop --start --delete] {image}*"

