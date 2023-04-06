#!/usr/bin/env bash
set -eux

source ./scripts/docker/bin/common.sh

function pull_image() {
    local local_tag="$1"
    local remote="${REGISTRY}/${local_tag}"

    docker pull "${remote}"
    docker tag "${remote}" "${local_tag}"
}

function push_image() {
    local local_tag="$1"
    local remote="${REGISTRY}/${local_tag}"

    docker tag "${local_tag}" "${remote}"
    docker push "${remote}"
}

# shellcheck disable=SC2015
[[ "${1:-}" == "push" ]] && {
    push_image "gci-dev"
} || {
    pull_image "gci-dev"
}
