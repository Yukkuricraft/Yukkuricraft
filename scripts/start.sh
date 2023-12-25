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

# Copy configs
if [[ ! -d "/yc-configs" ]]; then
    mkdir /yc-configs/
fi

debuglog "Copying /yc-default-configs/server to /yc-configs"
run cp /yc-default-configs/server/* /yc-configs/

debuglog "Copying /yc-server-configs to /yc-configs"
run cp /yc-server-configs/* /yc-configs/

if [[ ${TYPE} == "FORGE" || ${TYPE} == "FABRIC" ]]; then
    if [[ ! -d "/yc-configs/config" ]]; then
        mkdir /yc-configs/config/
    fi

    debuglog "Copying /modsconfig-bindmount to /yc-configs/config/"
    run cp /modsconfig-bindmount/* /yc-configs/config/
fi

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

function warn_ctrl_c {
    if [[ ! -f "/last_ctrl_c" ]]; then
        echo $(date -c) >> /last_ctrl_c
        echo "You just tried to send a TERM signal. Enter Ctrl+C twice within two seconds to propagate the TERM signal."
    fi
}

echo "###########################################################"
echo "STARTING ORIGINAL ITZG/DOCKER-MINECRAFT-SERVER START SCRIPT"
echo $(whoami)

exec /start