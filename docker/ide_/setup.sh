#!/bin/bash -i
set -eux

# Setup .bashrc (overwrite from dev layer)
cd "${DOTFILES_ROOT}" && ls
./setup.sh

# Update all configs
${DOTFILES_ROOT}/bin/update_configs

# Setup vim plugins (ignore vimrc errors, it's ok)
vim -E -s -u "~/.vimrc" +PlugInstall +qall || true

