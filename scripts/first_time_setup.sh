#!/usr/bin/env bash

CURR_UID=$(id -u)
CURR_GID=$(id -g)
REPO_ROOT=$(pwd)
USER=$(whoami)

# Make gitignore'd generated file directory
mkdir -p ${REPO_ROOT}/gen/velocity
mkdir -p ${REPO_ROOT}/gen/docker-compose
mkdir -p ${REPO_ROOT}/gen/env-toml
mkdir -p ${REPO_ROOT}/gen/env-files

# Sudo things
echo "gib sudo first"
sudo echo "ty"

# If on mac, don't mount /var/lib/yukkuricraft as data dir because >docker on mac
# (Smth smth /var path has extra perm requirements)
if [[ $(uname) == *"Darwin"* ]]; then
    BASE_PATH=/Users/${USER}/Documents/YC2.0
else
    BASE_PATH=/var/lib/yukkuricraft
fi
HOST_RESTIC_ROOT=${BASE_PATH}/restic

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

# Add MC_FS_ROOT which depends on Mac or not-Mac
echo "MC_FS_ROOT=${BASE_PATH}" >> ${LOCAL_ENV_FILE}
echo "HOST_RESTIC_ROOT=${HOST_RESTIC_ROOT}" >> ${LOCAL_ENV_FILE}

echo $(pwd)

docker run \
    -e RESTIC_REPOSITORY=/backups \
    -e RESTIC_PASSWORD_FILE=/restic.password \
    -v ${HOST_RESTIC_ROOT}:/backups \
    -v $(pwd)/secrets/restic.password:/restic.password \
    restic/restic \
    init