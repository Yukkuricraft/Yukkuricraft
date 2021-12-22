#!/bin/bash

echo "Poop"
echo "YC_ENV: $YC_ENV"

if [[ "$YC_ENV" == "prod" ]]; then
    echo "WE PROD";
    ln -s /worlds /yc-worlds
fi

if [[ "$YC_ENV" == "dev" ]]; then
    echo "WE DEV";
    rsync -uarP /worlds/* /yc-worlds/
    chown -R minecraft:minecraft /yc-worlds
fi

/start
