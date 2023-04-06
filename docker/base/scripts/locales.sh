#!/usr/bin/env bash
set -eux

apt-get update && apt-get install -y locales

sed -i -e "s/# $LANG.*/$LANG UTF-8/" /etc/locale.gen

dpkg-reconfigure --frontend=noninteractive locales

update-locale LANG="$LANG"
