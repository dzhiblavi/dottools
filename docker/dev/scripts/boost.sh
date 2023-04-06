#!/usr/bin/env bash
set -eux

BOOST_STRVER="${BOOST_VERSION//./_}"

# Install boost
wget "https://boostorg.jfrog.io/artifactory/main/release/${BOOST_VERSION}/source/boost_${BOOST_STRVER}.tar.gz"
tar xf "boost_${BOOST_STRVER}.tar.gz" --no-same-owner && cd "boost_${BOOST_STRVER}"
./bootstrap.sh --with-python="$(command -v python3)" && ./b2 -j "$(nproc)" install
