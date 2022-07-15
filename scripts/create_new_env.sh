#!/usr/bin/env bash

python src/generator/new_dev_env_gen.py


# Replace with py script???

exit 1

# Creates necessary files and folders to run a new environment.
# For now just copies env/prod.env to the new env config file. Modify as needed. Will need to adjust VELOCITY_PORT manually.

if [ -z ${ENV+x} ]; then
    echo "Must set environment variable 'ENV'. Was unset."
    exit 1
fi

BASE=/var/lib/yukkuricraft/env/${ENV}

# Create docker fs mount points

echo "Generating 'plugins', 'worlds', and 'certs' folders in ${BASE}"
sudo mkdir -p ${BASE}/plugins
sudo mkdir -p ${BASE}/worlds
sudo mkdir -p ${BASE}/certs

echo "chown'ing ${BASE} to minecraft:minecraft"
sudo chown -R minecraft:minecraft ${BASE}


# Create env file

echo "Copying env/prod.env to env/${ENV}.env"
cp env/prod.env env/${ENV}.env
sed -i "s/ENV=prod/ENV=${ENV}/g" env/${ENV}.env

(
  (
    echo "#";
    echo "# THIS FILE WAS CREATED VIA SCRIPT USING PROD'S CONFIG AS THE BASE";
    echo "# WILL NEED TO MODIFY VELOCITY_PORT MANUALLY";
    echo "#";
    echo "";
  ) \
   && cat env/${ENV}.env \
) > tmp_file \
  && mv tmp_file env/${ENV}.env

# Create folders for configs in secrets

SECRETS_CONFIG_PATH=secrets/configs/dev1/worlds/

sudo mkdir -p ${BASE}/${SECRETS_CONFIG_PATH}

