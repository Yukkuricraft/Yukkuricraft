#!/usr/bin/env bash

sync() {
  mc-image-helper sync-and-interpolate \
    --skip-newer-in-destination \
    --replace-env-file-suffixes=yml,yaml,txt,cfg,conf,properties,hjson,json,tml,toml \
    --replace-env-excludes= \
    --replace-env-exclude-paths= \
    --replace-env-prefix=CFG_ \
    $1 \
    $2
}

sync $COPY_MODS_SRC $COPY_MODS_DEST
sync $COPY_PLUGINS_SRC $COPY_PLUGINS_DEST
sync $COPY_CONFIG_SRC $COPY_CONFIG_DEST
