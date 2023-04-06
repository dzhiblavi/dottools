FROM nvidia/cuda:11.6.0-cudnn8-devel-ubuntu20.04

# From base/Dockerfile
ARG user
ARG group
ARG uid
ARG gid
ARG DEBIAN_FRONTEND=nointeractive

ENV DKR_USER=${user}
ENV DKR_GROUP=${group}
ENV DKR_UID=${uid}
ENV DKR_GID=${gid}

# Add user
ADD docker/base/mkuser.sh /tmp/dkr/base/mkuser.sh
RUN /tmp/dkr/base/mkuser.sh

# Install basic tools
ADD docker/base/tools.sh /tmp/dkr/base/tools.sh
RUN /tmp/dkr/base/tools.sh

# From dev/Dockerfile
ARG mount_dir=dkr-mount

ENV DOCKER_MNT_DIR_NAME=${mount_dir}
ENV TERM=xterm-256color

# Install tools
ADD docker/dev/tools.sh /tmp/dkr/dev/tools.sh
RUN /tmp/dkr/dev/tools.sh

# Switch to user
USER ${DKR_USER}

# Install & prepare vim
ADD docker/dev/vim_setup.sh /tmp/dkr/dev/vim_setup.sh
RUN /tmp/dkr/dev/vim_setup.sh

ADD docker/dev/bashrc /home/${DKR_USER}/.bashrc

WORKDIR /home/${DKR_USER}

ENV DKR_IMAGE_NAME=cuda

