#!/bin/bash

echo "Poop"
echo "YC_ENV: $YC_ENV"
echo "MOTD: $MOTD"

if [[ "$YC_ENV" == "prod" ]]; then
    echo "WE PROD";
    ln -s /worlds-bindmount /yc-worlds
fi

if [[ "$YC_ENV" == "dev" ]]; then
    echo "WE DEV";
    echo "COPY_PROD_WORLD: $COPY_PROD_WORLD"
    if [[ ! -z "$COPY_PROD_WORLD" ]]; then
        echo '>>> rsync -arP /worlds-bindmount/ /worlds-volume'
        rsync -arP /worlds-bindmount/ /worlds-volume
    fi

    ls -al /
    echo '>>> ln -s /worlds-volume /yc-worlds'
    ln -s /worlds-volume /yc-worlds
    echo '>>> chown -R minecraft:minecraft /yc-worlds'
    chown -R minecraft:minecraft /yc-worlds
    ls -al /
fi


if [[ ! -s "/data/server.properties" ]]; then
    cp /config/server.properties /data/server.properties
fi
if ! grep -q "motd" /data/server.properties; then
    echo "motd=$MOTD" >> /data/server.properties
fi

/start
