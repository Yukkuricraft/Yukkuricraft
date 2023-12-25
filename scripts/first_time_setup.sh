#!/usr/bin/env bash

echo "gib sudo first"
sudo echo "ty"

BASE_PATH=/var/lib/yukkuricraft

CURR_UID=$(id -u)
CURR_GID=$(id -g)

sudo mkdir -p ${BASE_PATH}/db
sudo mkdir -p ${BASE_PATH}/env
sudo mkdir -p ${BASE_PATH}/nginx

sudo chown -R ${CURR_UID}:${CURR_GID} ${BASE_PATH}/env