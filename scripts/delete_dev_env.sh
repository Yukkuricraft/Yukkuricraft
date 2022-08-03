#!/usr/bin/env bash

# Creates necessary files and folders to run a new environment.
# For now just copies env/prod.env to the new env config file. Modify as needed.

run_sudo() {
    log ">>> $@"
    sudo $@
}

log() {
    echo "[$(date +"%Y-%m-%d_%H-%M")] $@"
}

if [ -z ${ENV+x} ]; then
    log "Must set environment variable 'ENV'. Was unset."
    exit 1
fi

if [ ${ENV} == 'prod' ]; then
    log ""
    log "Are you dumb?"
    log "Please don't delete prod."
    log ""
    exit 9
fi


# Delete ENV folder in /var/lib/yukkuricraft/env
BASE=/var/lib/yukkuricraft/env/${ENV}
if [ -d ${BASE} ]; then
    log ""
    log "Deleting ${BASE}..."
    run_sudo rm -r ${BASE}
    log "Done."
fi


# Delete ENV.toml
ENV_FILE=env/${ENV}.toml
if [ -f ${ENV_FILE} ]; then
    log ""
    log "Deleting env file..."
    run_sudo rm "${ENV_FILE}"
    log "Done."
fi


# Delete everything under secrets/configs/ENV (nginx + world group configs)
SECRETS_DIR=secrets/configs/${ENV}
if [ -d ${SECRETS_DIR} ]; then
    log ""
    log "Deleting config secrets..."
    run_sudo rm -r "${SECRETS_DIR}"
    log "Done."
fi


