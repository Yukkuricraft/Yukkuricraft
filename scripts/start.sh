#!/bin/bash

function debuglog {
    if [[ ! -z "$DEBUG" && ( "$DEBUG" == "1" || "$DEBUG" == "true" ) ]]; then echo $@; fi
}

function run {
    debuglog ">>>" $@
    $@
}

declare -A symlinkmap
function create_symlinks {
    debuglog "@@@@@@ ATTEMPTING TO CREATE SYMLINKS"
    local -n data=$1
    for src in "${!data[@]}"; do
        debuglog $src
        debuglog "${data[$src]}"

        debuglog "Checking if symlink ${data[$src]} exists already..."
        if [[ -L "${data[$src]}" ]]; then
            debuglog "Symlink exists - deleting."
            run rm "${data[$src]}"
        fi

        debuglog "Ensuring symlink dest ${data[$src]} isn't a regular dir/file..."
        if [[ ! -s "${data[$src]}" ]]; then
            debuglog "Listing src"
            ls -al ${src}

            debuglog "Symlinking ${src} to ${data[$src]}"
            run ln -s ${src} ${data[$src]}
        fi
    done
}

# START FLOW
debuglog "RUNNING AS: $(whoami)"
debuglog "MOTD: $MOTD"
debuglog "UID: $UID"
debuglog "GID: $GID"
debuglog "SERVER TYPE: $TYPE"


echo "################################################"
echo "STARTING CUSTOM YC/MINECRAFT-SERVER START SCRIPT"

# run mkdir /data/logs
# run touch /data/logs/latest.log
run find /worlds-bindmount/ -name session.lock -type f -delete

# We use `bukkit.yml` to set the world path to the bindmount. If not bukkit/paper, we need to symlink.
# Atm we only deal with bukkit/paper and forge/fabric. Not sure about other server types.
if [[ ${TYPE} != "PAPER" && ${TYPE} != "BUKKIT" ]]; then
    symlinkmap["/worlds-bindmount"]="/data/world"
    create_symlinks symlinkmap
fi

source /scripts/server_type_actions.sh
source /scripts/merge_configs_into_yc_configs.sh

# Chowns
debuglog "Chown /data to ${UID}:${GID}"
run chown -R ${UID}:${GID} /data

run chown -R ${UID}:${GID} /plugins-bindmount
run chown -R ${UID}:${GID} /worlds-bindmount
run chown -R ${UID}:${GID} /mods-bindmount
run chown -R ${UID}:${GID} /modsconfig-bindmount

echo "==============="
run ls -al /
run ls -al /data

echo "###########################################################"
echo "STARTING ORIGINAL ITZG/DOCKER-MINECRAFT-SERVER START SCRIPT"
echo $(whoami)

exec /start