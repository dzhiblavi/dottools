#!/usr/bin/env bash
set -eux

# GLog
git clone https://github.com/google/glog.git && cd glog
cmake -S . -B build -G "Unix Makefiles"
cmake --build build -- -j "$(nproc)"
cmake --build build --target install
