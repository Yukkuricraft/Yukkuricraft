#!/bin/bash

function debuglog {
    if [[ ! -z "$DEBUG" && ( "$DEBUG" == "1" || "$DEBUG" == "true" ) ]]; then echo $@; fi
}
debuglog "Poop"
debuglog "YC_ENV: $YC_ENV"
debuglog "MOTD: $MOTD"

if [[ "$YC_ENV" == "prod" ]]; then
    debuglog "WE PROD";
    ln -s /worlds-bindmount /yc-worlds
fi

if [[ "$YC_ENV" == "dev" ]]; then
    debuglog "WE DEV";
    debuglog "COPY_PROD_WORLD: $COPY_PROD_WORLD"
    if [[ ! -z "$COPY_PROD_WORLD" ]]; then
        debuglog '>>> rsync -arP /worlds-bindmount/ /worlds-volume'
        rsync -arP /worlds-bindmount/ /worlds-volume
    fi

    debuglog '>>> ln -s /worlds-volume /yc-worlds'
    ln -s /worlds-volume /yc-worlds

    debuglog '>>> chown -R minecraft:minecraft /yc-worlds'
    chown -R minecraft:minecraft /yc-worlds

    # If dev env, use the MOTD passed in from docker-compose which gives us useful info.
    # If prod, just copy `minecraft-data/configs/server.properties` wholesale and don't do anything extra.
    if [[ ! -s "/data/server.properties" ]]; then
        cp /config/server.properties /data/server.properties
    fi
    if ! grep -q "motd" /data/server.properties; then
        echo "motd=$MOTD" >> /data/server.properties
    fi
fi


/start
