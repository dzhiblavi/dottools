#!/bin/bash -i
set -eux

useradd --uid "${DKR_UID}" --shell /bin/bash --create-home "${DKR_USER}"

adduser "${DKR_USER}" sudo && passwd -d "${DKR_USER}"
