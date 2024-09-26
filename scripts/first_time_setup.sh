#!/usr/bin/env bash

CURR_UID=$(id -u)
CURR_GID=$(id -g)

echo "gib sudo first"
sudo echo "ty"

BASE_PATH=/var/lib/yukkuricraft

sudo mkdir -p ${BASE_PATH}/db
sudo mkdir -p ${BASE_PATH}/env
sudo mkdir -p ${BASE_PATH}/nginx

sudo chown -R ${CURR_UID}:${CURR_GID} ${BASE_PATH}

cp envs/localhost.env.template envs/localhost.env
echo "" >> envs/localhost.env
echo "YC_REPO_ROOT=$(pwd)" >> envs/localhost.env