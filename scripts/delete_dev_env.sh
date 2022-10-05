#!/usr/bin/env bash

run() {
    log ">>> $@"
    $@
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
    log "Please don't delete prod. :("
    log ""
    exit 9
fi


# Delete ENV folder in /var/lib/yukkuricraft/env
BASE=/var/lib/yukkuricraft/env/${ENV}
if [ -d ${BASE} ]; then
    log ""
    log "Deleting ${BASE}..."
    run rm -r ${BASE}
    log "Done."
fi


# Delete ENV.toml
ENV_FILE=env/${ENV}.toml
if [ -f ${ENV_FILE} ]; then
    log ""
    log "Deleting env file..."
    run rm "${ENV_FILE}"
    log "Done."
fi

# Delete any generated files
DOCKER_COMPOSE_FILE=gen/docker-compose-${ENV}.yml
VELOCITY_FILE=gen/velocity-${ENV}.toml
if [ -f ${DOCKER_COMPOSE_FILE} ]; then
    log ""
    log "Deleting generated files..."
    run rm ${DOCKER_COMPOSE_FILE}
    run rm ${VELOCITY_FILE}
    log "Done."
fi



# Delete everything under secrets/configs/ENV (nginx + world group configs)
SECRETS_DIR=secrets/configs/${ENV}
if [ -d ${SECRETS_DIR} ]; then
    log ""
    log "Deleting config secrets..."
    run rm -r "${SECRETS_DIR}"
    log "Done."
fi


