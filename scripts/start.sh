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

function copy_configs {
    debuglog "Copying /yc-default-configs/server to /data"
    run cp /yc-default-configs/server/* /data/

    debuglog "Copying /yc-server-configs to /data"
    run cp /yc-server-configs/* /data/
}

# START FLOW
debuglog "RUNNING AS: $(whoami)"
debuglog "YC_ENV: $YC_ENV"
debuglog "MOTD: $MOTD"
debuglog "COPY_PROD_WORLD: $COPY_PROD_WORLD"
debuglog "COPY_PROD_PLUGINS: $COPY_PROD_PLUGINS"
debuglog "UID: $UID"
debuglog "GID: $GID"


echo "################################################"
echo "STARTING CUSTOM YC/MINECRAFT-SERVER START SCRIPT"

run mkdir /data/logs
run touch /data/logs/latest.log

run find /yc-worlds/ -name session.lock -type f -delete

run echo "YC_ENV=$YC_ENV"
run echo "DEV_AS_PROD_OVERRIDE=$DEV_AS_PROD_OVERRIDE"
if [[ "$YC_ENV" == "prod" || x"$DEV_AS_PROD_OVERRIDE" == x"true" ]]; then
    symlinkmap["/worlds-bindmount"]="/yc-worlds"
    symlinkmap["/plugins-bindmount"]="/data/plugins"

    debuglog "WE PROD - $YC_ENV - $DEV_AS_PROD_OVERRIDE";
    create_symlinks symlinkmap

    copy_configs

    debuglog "Chown /data to ${UID}:${GID}"
    run chown -R ${UID}:${GID} /data

    run chown -R ${UID}:${GID} /plugins-bindmount
    run chown -R ${UID}:${GID} /worlds-bindmount
    run chown -R ${UID}:${GID} /mods-bindmount
    run chown -R ${UID}:${GID} /modsconfig-bindmount

    echo "==============="
    ls -al /
    ls -al /data
elif [[ "$YC_ENV" == "dev" ]]; then
    ## Symlinks
    symlinkmap["/worlds-volume-dev"]="/yc-worlds"
    run rm /data/plugins # Please refactor this...
    symlinkmap["/plugins-volume-dev"]="/data/plugins"

    debuglog "WE DEV";
    create_symlinks symlinkmap

    copy_configs

    ## Chowns
    for vol in ${!symlinkmap[@]}; do
        run chown -R $UID:$GID ${vol}
    done

    ## Copying prod data
    if [[ ! -z "$COPY_PROD_WORLD" ]]; then
        run rsync -arP /worlds-bindmount/ /yc-worlds
    fi

    if [[ ! -z "$COPY_PROD_PLUGINS" ]]; then
        ignored_plugins=(
            --exclude='dynmap'
        )
        run rsync -arP  /plugins-bindmount/ /plugins-volume-dev "${ignored_plugins[@]}"
    fi

    ## Configs
    # If dev env, use the MOTD passed in from docker-compose which gives us useful info.
    # If prod, just copy `minecraft-data/configs/server.properties` wholesale and don't do anything extra.
    if [[ ! -s "/data/server.properties" ]]; then
        run cp /yc-server-configs/server.properties /data/server.properties
    fi
    if ! grep -q "motd" /data/server.properties; then
        echo "motd=$MOTD" >> /data/server.properties # Don't use 'run' - the >> is processed after the 'run' so it also appends debug echos.
    fi
fi

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