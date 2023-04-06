#!/usr/bin/env bash
set -eux

[[ -d ".git" ]] || {
    echo "Should be executed from repository root (.git not found)" && exit 1
}

DEV_TAG="gci-dev"
DOCKER_MNT_DIR_NAME="dkr-mount"
BUILD_ARGS=$(                                          \
    printf "%s"                                        \
        "--build-arg mount_dir=${DOCKER_MNT_DIR_NAME}" \
)

# shellcheck disable=SC2086
docker build                          \
    -t "${DEV_TAG}"                   \
    -f scripts/docker/dev/Dockerfile  \
    ${BUILD_ARGS} .
