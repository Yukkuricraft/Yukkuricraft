#!/usr/bin/env bash

CURR_UID=$(id -u)
CURR_GID=$(id -g)
REPO_ROOT=$(pwd)

# Make gitignore'd generated file directory
mkdir -p ${REPO_ROOT}/gen/velocity
mkdir -p ${REPO_ROOT}/gen/docker-compose
mkdir -p ${REPO_ROOT}/gen/env-toml
mkdir -p ${REPO_ROOT}/gen/env-files

# Sudo things
echo "gib sudo first"
sudo echo "ty"

BASE_PATH=/var/lib/yukkuricraft

# Make dirs
sudo mkdir -p ${BASE_PATH}/db
sudo mkdir -p ${BASE_PATH}/env
sudo mkdir -p ${BASE_PATH}/nginx

# Make empty filebrowser db file so docker can mount it
sudo touch ${BASE_PATH}/db/filebrowser.db

# Ensure correct ownership
sudo chown -R ${CURR_UID}:${CURR_GID} ${BASE_PATH}

# Create localhost env file to be used with web docker compose
LOCAL_ENV_FILE=envs/localhost.env
cp envs/localhost.env.template ${LOCAL_ENV_FILE}
echo "" >> envs/localhost.env
echo "YC_REPO_ROOT=${REPO_ROOT}" >> ${LOCAL_ENV_FILE}


# Add UID/GID's for use with filebrowser/filebrowser's image
echo "UID=${CURR_UID}" >> ${LOCAL_ENV_FILE}
echo "GID=${CURR_GID}" >> ${LOCAL_ENV_FILE}