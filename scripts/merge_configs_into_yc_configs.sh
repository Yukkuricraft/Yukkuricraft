#!/usr/bin/env bash

function debuglog {
    if [[ ! -z "$DEBUG" && ( "$DEBUG" == "1" || "$DEBUG" == "true" ) ]]; then echo $@; fi
}

function run {
    debuglog ">>>" $@
    $@
}

#
# How does /yc-configs work?
# We copy the entire contents, including directory structure, and drop it into the container's `/data` dir.
#
# This means 'server configs' which are "rooted" at `/data` such as `/data/server.properties` will live in `/yc-configs/server.properties`
#   Likewise something that needs to be moved to `/data/mods/my_mod/config.yaml` would live in `/yc-configs/mods/my_mod/config.yaml`
#

YC_CONFIGS_DIR="/yc-configs/"
if [[ ! -d $YC_CONFIGS_DIR ]]; then
    mkdir $YC_CONFIGS_DIR
fi

#
# Server configs
#

debuglog "Copying /defaultconfigs-bindmount/server to $YC_CONFIGS_DIR"
run cp -rv /defaultconfigs-bindmount/server/* $YC_CONFIGS_DIR

debuglog "Copying /serverconfig-bindmount to $YC_CONFIGS_DIR"
run cp -rv  /serverconfig-bindmount/* $YC_CONFIGS_DIR

#
# Plugin configs
#

if [[ ${TYPE} == "BUKKIT" || ${TYPE} == "PAPER" ]]; then
    PLUGIN_CONFIGS_DIR="${YC_CONFIGS_DIR}plugins/"
    if [[ ! -d $PLUGIN_CONFIGS_DIR ]]; then
        mkdir $PLUGIN_CONFIGS_DIR
    fi

    debuglog "Copying /defaultconfigs-bindmount/plugins to ${PLUGIN_CONFIGS_DIR}"
    run cp -rv /defaultconfigs-bindmount/plugins/* $PLUGIN_CONFIGS_DIR

    debuglog "Copying /pluginsconfig-bindmount to ${PLUGIN_CONFIGS_DIR}"
    run cp -rv  /pluginsconfig-bindmount/* $PLUGIN_CONFIGS_DIR
fi

#
# Mod configs
#

if [[ ${TYPE} == "FORGE" || ${TYPE} == "FABRIC" ]]; then
    MOD_CONFIGS_DIR="${YC_CONFIGS_DIR}config/"
    if [[ ! -d $MOD_CONFIGS_DIR ]]; then
        mkdir $MOD_CONFIGS_DIR
    fi

    debuglog "Copying /defaultconfigs-bindmount/mods to ${MOD_CONFIGS_DIR}"
    run cp -rv /defaultconfigs-bindmount/mods/* $MOD_CONFIGS_DIR

    debuglog "Copying /modsconfig-bindmount to ${MOD_CONFIGS_DIR}"
    run cp -rv /modsconfig-bindmount/* $MOD_CONFIGS_DIR
fi