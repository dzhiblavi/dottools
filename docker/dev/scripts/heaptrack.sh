#!/usr/bin/env bash
set -eux

# Install heaptrack
git clone https://github.com/KDE/heaptrack.git && cd heaptrack && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release && make -j "$(nproc)"
make install
