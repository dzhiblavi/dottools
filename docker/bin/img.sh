#!/bin/bash -i
set -e

br_import 'print'

BASE_BUILD_ARGS=$(                    \
    printf "%s %s %s %s"              \
        "--build-arg user=$(id -un)"  \
        "--build-arg group=$(id -gn)" \
        "--build-arg uid=$(id -u)"    \
        "--build-arg gid=$(id -g)"    \
)

DEV_BUILD_ARGS=$(                                      \
    printf "%s"                                        \
        "--build-arg mount_dir=${DOCKER_MNT_DIR_NAME}" \
)

IDE_BUILD_ARGS=$(                            \
    printf "%s %s"                           \
        "--build-arg dots_dir_host=."        \
        "--build-arg dots_dir_name=dotfiles" \
)

CUDA_BUILD_ARGS=$(           \
    printf "%s %s"           \
        "${BASE_BUILD_ARGS}" \
        "${DEV_BUILD_ARGS}"  \
)

REGISTRY="cr.yandex/crps3mi5urdae0psl2kr"

function execute() {
    [[ ${DRYRUN:-0} -eq 1 ]] && { print_info "$@"; } || { $@; }
}

function build_image() {
    execute "docker build -t ${IMAGE_NAME} -f docker/${IMAGE_NAME}/Dockerfile ${BUILD_ARGS} ."
}

function pull_image() {
    local remote="${REGISTRY}/${IMAGE_NAME}"
    local local_tag="${IMAGE_NAME}"

    execute "docker pull ${remote}"
    execute "docker tag ${remote} ${local_tag}"
}

function push_image() {
    local remote="${REGISTRY}/${IMAGE_NAME}"
    local local_tag="${IMAGE_NAME}"

    execute "docker tag ${local_tag} ${remote}"
    execute "docker push ${remote}"
}

function show_images_status() {
    docker image ls
}

function images_main() {
    [[ $# -eq 0 ]] && { show_images_status; print_info "${IMAGES_USAGE}"; return 1; }

    IMAGES=()
    while [[ -n "$1" ]]; do
        case "$1" in
            base*) {
                IMAGES+=("$1")
                BUILD_ARGS="${BASE_BUILD_ARGS}"
            } ;;
            dev*) {
                IMAGES+=("$1")
                BUILD_ARGS="${DEV_BUILD_ARGS}"
            } ;;
            ide*) {
                IMAGES+=("$1")
                BUILD_ARGS="${IDE_BUILD_ARGS}"
            } ;;
            cuda*) {
                IMAGES+=("$1")
                BUILD_ARGS="${CUDA_BUILD_ARGS}"
            } ;;
            '-?'|--status) {
                show_images_status
            } ;;
            -b|--build) {
                BUILD=1
            } ;;
            --pull) {
                PULL=1
            } ;;
            --push) {
                PUSH=1
            } ;;
            -d|--dry-run) {
                DRYRUN=1
            } ;;
            *) {
                print_error "No such option: '$1'"
            } ;;
        esac
        shift
    done

    for IMAGE_NAME in "${IMAGES[@]}"; do
        print_info "Image: ${IMAGE_NAME}"
        [[ ${PULL-0}  -eq 1 ]] && pull_image
        [[ ${BUILD-0} -eq 1 ]] && build_image
        [[ ${PUSH-0}  -eq 1 ]] && push_image
    done
}

IMAGES_USAGE='[-d|--dry-run -b|--build --pull --push] {image}+'

