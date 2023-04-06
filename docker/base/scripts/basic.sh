#!/usr/bin/env bash
set -eux

apt update && apt upgrade -y
apt install -y software-properties-common && rm -rf /var/lib/apt/lists/*

add-apt-repository -y ppa:ubuntu-toolchain-r/test
apt install -y curl wget make git tar sudo
