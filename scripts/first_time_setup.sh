#!/usr/bin/env bash

CURR_UID=$(id -u)
CURR_GID=$(id -g)

echo "gib sudo first"
sudo echo "ty"

BASE_PATH=/var/lib/yukkuricraft

# Make dirs
sudo mkdir -p ${BASE_PATH}/db
sudo mkdir -p ${BASE_PATH}/env
sudo mkdir -p ${BASE_PATH}/nginx

# Make empty filebrowser db file so docker can mount it
touch ${BASE_PATH}/db/filebrowser.db

# Ensure correct ownership
sudo chown -R ${CURR_UID}:${CURR_GID} ${BASE_PATH}

# Create localhost env file to be used with web docker compose
cp envs/localhost.env.template envs/localhost.env
echo "" >> envs/localhost.env
echo "YC_REPO_ROOT=$(pwd)" >> envs/localhost.env