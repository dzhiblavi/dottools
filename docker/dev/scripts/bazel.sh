#!/usr/bin/env bash
set -eux

# Install Bazel
curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor > bazel.gpg
mv bazel.gpg /etc/apt/trusted.gpg.d/
echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" \
    | tee /etc/apt/sources.list.d/bazel.list
apt update -y && apt install -y bazel

# Install bazel-compdb
(
  cd "${BAZEL_COMPDB_INSTALL_DIR}" \
  && curl -L "https://github.com/grailbio/bazel-compilation-database/archive/${BAZEL_COMPDB_VERSION}.tar.gz" | tar -xz \
  && ln -f -s "${BAZEL_COMPDB_INSTALL_DIR}/bazel-compilation-database-${BAZEL_COMPDB_VERSION}/generate.py" bazel-compdb
)
