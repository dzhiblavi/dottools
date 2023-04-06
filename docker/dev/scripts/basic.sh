#!/usr/bin/env bash
set -eux

cd /tmp

apt update && apt upgrade -y

# Tools
apt install -y \
    curl gnupg apt-transport-https pkg-config \
    python3 python3-dev

# Libs
apt install -y \
    libunwind-dev lzma-dev zlib1g-dev libtbb-dev \
    libcurl4-gnutls-dev libssl-dev libpython3-all-dev

# Development
apt install -y                                        \
    clangd-15 clang-format-15 clang-format clang-tidy \
    htop glances tree shellcheck doxygen graphviz
