#!/usr/bin/env bash
set -eux

[[ -d ".git" ]] || {
    echo "Should be executed from repository root (.git not found)" && exit 1
}

BASE_TAG="gci-base"
BUILD_ARGS=$(                         \
    printf "%s %s %s %s"              \
        "--build-arg user=$(id -un)"  \
        "--build-arg group=$(id -g)"  \
        "--build-arg uid=$(id -u)"    \
        "--build-arg gid=$(id -g)"    \
)

# shellcheck disable=SC2086
docker build                          \
    -t "${BASE_TAG}"                  \
    -f scripts/docker/base/Dockerfile \
    ${BUILD_ARGS} .
