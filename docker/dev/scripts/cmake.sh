#!/usr/bin/env bash
set -eux

# Install CMake
wget "https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}.tar.gz"
tar xvf "cmake-${CMAKE_VERSION}.tar.gz" --no-same-owner && cd "cmake-${CMAKE_VERSION}"
./configure --parallel="$(nproc)" && make -j "$(nproc)" && make install
