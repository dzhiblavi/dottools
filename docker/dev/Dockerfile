FROM dev/base AS base

ARG mount_dir=dkr-mount

ENV TERM=xterm-256color
ENV DOCKER_MNT_DIR_NAME=${mount_dir}
ENV DKR_IMAGE_NAME=dev

ADD scripts/docker/dev/scripts/basic.sh /tmp/dkr/dev/scripts/basic.sh
RUN /tmp/dkr/dev/scripts/basic.sh

ADD scripts/docker/dev/scripts/bazel.sh /tmp/dkr/dev/scripts/bazel.sh
RUN BAZEL_COMPDB_VERSION="0.5.2" BAZEL_COMPDB_INSTALL_DIR="/usr/local/bin" /tmp/dkr/dev/scripts/bazel.sh

ADD scripts/docker/dev/scripts/cmake.sh /tmp/dkr/dev/scripts/cmake.sh
RUN CMAKE_VERSION="3.25.0-rc1" /tmp/dkr/dev/scripts/cmake.sh

ADD scripts/docker/dev/scripts/perf.sh /tmp/dkr/dev/scripts/perf.sh
RUN /tmp/dkr/dev/scripts/perf.sh

ADD scripts/docker/dev/scripts/boost.sh /tmp/dkr/dev/scripts/boost.sh
RUN BOOST_VERSION="1.81.0" /tmp/dkr/dev/scripts/boost.sh

ADD scripts/docker/dev/scripts/protobuf.sh /tmp/dkr/dev/scripts/protobuf.sh
RUN PROTOBUF_VERSION="3.14.0" /tmp/dkr/dev/scripts/protobuf.sh

ADD scripts/docker/dev/scripts/benchmark.sh /tmp/dkr/dev/scripts/benchmark.sh
RUN /tmp/dkr/dev/scripts/benchmark.sh

ADD scripts/docker/dev/scripts/glog.sh /tmp/dkr/dev/scripts/glog.sh
RUN /tmp/dkr/dev/scripts/glog.sh

ADD scripts/docker/dev/scripts/heaptrack.sh /tmp/dkr/dev/scripts/heaptrack.sh
RUN /tmp/dkr/dev/scripts/heaptrack.sh

USER ${DKR_USER}
ADD --chown=${DKR_USER}:${DKR_GROUP} scripts/docker/dev/bashrc /home/${DKR_USER}/.bashrc

WORKDIR /home/${DKR_USER}
