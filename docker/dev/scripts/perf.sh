#!/usr/bin/env bash
set -eux

# Install perf's deps for most functionality
apt-get install -y \
    flex bison libelf-dev libbfd-dev libcap-dev libnuma-dev libperl-dev \
    python3-dev libunwind-dev libz-dev liblzma-dev libzstd-dev libdw-dev python3-pip

# Install perf
pip3 install setuptools
git clone --depth 1 https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux/tools/perf && make -j "$(nproc)" && cp perf /usr/bin
