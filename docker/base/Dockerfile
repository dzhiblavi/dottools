FROM ubuntu:20.04 as base

ARG user
ARG group
ARG uid
ARG gid
ARG DEBIAN_FRONTEND=nointeractive

ENV DKR_USER=${user}
ENV DKR_GROUP=${group}
ENV DKR_UID=${uid}
ENV DKR_GID=${gid}
ENV DKR_IMAGE_NAME=base

ADD scripts/docker/base/scripts/mkuser.sh /tmp/dkr/base/scripts/mkuser.sh
RUN /tmp/dkr/base/scripts/mkuser.sh

ADD scripts/docker/base/scripts/basic.sh /tmp/dkr/base/scripts/basic.sh
RUN /tmp/dkr/base/scripts/basic.sh

ADD scripts/docker/base/scripts/locales.sh /tmp/dkr/base/scripts/locales.sh
RUN LANG="en_US.UTF-8" /tmp/dkr/base/scripts/locales.sh 

ADD scripts/docker/base/scripts/gcc.sh /tmp/dkr/base/scripts/gcc.sh
RUN GCC_VERSION=11 /tmp/dkr/base/scripts/gcc.sh

ADD scripts/docker/base/scripts/clang.sh /tmp/dkr/base/scripts/clang.sh
RUN CLANG_VERSION=15 /tmp/dkr/base/scripts/clang.sh
