#!/usr/bin/env bash

echo ">> Syncing plugin configs back to bindmount..."
rsync -av --exclude '*.jar' /data/plugins/ /pluginsconfig-bindmount

echo ">> Syncing mod configs back to bindmount..."
rsync -av --exclude '*.jar' /data/config/ /modsconfig-bindmount

echo ">> Syncing server configs back to bindmount..."
rsync -arv --exclude '/*/' --exclude '.*' --exclude "*.txt" --exclude "*.jar" /data/ /serverconfig-bindmount