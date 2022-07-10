#!/usr/bin/env bash

# Creates necessary files and folders to run a new environment.
# For now just copies env/prod.env to the new env config file. Modify as needed.

if [ -z ${ENV+x} ]; then
    echo "Must set environment variable 'ENV'. Was unset."
    exit 1
fi

BASE=/var/lib/yukkuricraft/${ENV}

echo "Generating 'plugins', 'worlds', and 'certs' folders in ${BASE}"
sudo mkdir -p ${BASE}/plugins
sudo mkdir -p ${BASE}/worlds
sudo mkdir -p ${BASE}/certs

echo "chown'ing ${BASE} to minecraft:minecraft"
sudo chown -R minecraft:minecraft ${BASE}

echo "Copying env/prod.env to env/${ENV}.env"
cp env/prod.env env/${ENV}.env
