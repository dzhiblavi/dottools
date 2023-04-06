#!/usr/bin/env bash
set -eux

# Install google protobuf
wget "https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOBUF_VERSION}/protobuf-all-${PROTOBUF_VERSION}.tar.gz"
tar xvf "protobuf-all-${PROTOBUF_VERSION}.tar.gz" --no-same-owner && cd "protobuf-${PROTOBUF_VERSION}"
./configure && make -j "$(nproc)" && make install && ldconfig
