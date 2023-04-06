FROM dev/dev as base

USER ${DKR_USER}

ARG dots_dir_host
ARG dots_dir_name=dotfiles

ENV DOTFILES_ROOT=/home/${DKR_USER}/${dots_dir_name}

ADD --chown=${DKR_USER}:${DKR_GROUP} ${dots_dir_host} /home/${DKR_USER}/${dots_dir_name}
ADD docker/ide/setup.sh /tmp/dkr/ide/setup.sh

RUN /tmp/dkr/ide/setup.sh

ENV DKR_IMAGE_NAME=ide

