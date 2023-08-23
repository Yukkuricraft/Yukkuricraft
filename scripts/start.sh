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
        if [[ ! -s "${data[$src]}" ]]; then
            debuglog "Listing src"
            ls -al ${src}
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

echo "################################################"
echo "STARTING CUSTOM YC/MINECRAFT-SERVER START SCRIPT"

run mkdir /data/logs
run touch /data/logs/latest.log

if [[ "$YC_ENV" == "prod" ]]; then
    symlinkmap["/worlds-bindmount-prod"]="/yc-worlds"
    symlinkmap["/plugins-bindmount-prod"]="/data/plugins"

    debuglog "WE PROD";
    create_symlinks symlinkmap

    copy_configs

    debuglog "Chown /data to ${UID}:${GID}:"
    run chown -R ${UID}:${GID} /data

    echo "==============="
    ls -al /
    ls -al /data
fi

if [[ "$YC_ENV" == "dev" ]]; then
    ## Symlinks
    #symlinkmap["/worlds-volume-dev"]="/yc-worlds"

    run rm /data/plugins # Please refactor this...
    symlinkmap["/plugins-volume-dev"]="/data/plugins"

    debuglog "WE DEV";
    create_symlinks symlinkmap

    copy_configs

    ## Chowns
    for vol in ${!symlinkmap[@]}; do
        run chown -R minecraft:minecraft ${vol}
    done

    ## Copying prod data
    if [[ ! -z "$COPY_PROD_WORLD" ]]; then
        run rsync -arP /worlds-bindmount-prod/ /yc-worlds
    fi

    if [[ ! -z "$COPY_PROD_PLUGINS" ]]; then
        ignored_plugins=(
            --exclude='dynmap'
        )
        run rsync -arP  /plugins-bindmount-prod/ /plugins-volume-dev "${ignored_plugins[@]}"
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

trap '' TERM INT # Don't let ctrl+c stop the server. Use ctrl+p, then ctrl+q. Standard docker "detach" sequence.

echo "###########################################################"
echo "STARTING ORIGINAL ITZG/DOCKER-MINECRAFT-SERVER START SCRIPT"
echo $(whoami)

/start
