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
# We technically could just move the mods into `/data/mods`/plugins into `/data/plugins`, but since we're trying to explicitly
# build on top of `itzg/minecraft` as a layer, we'll move things into `/yc-mods` and let
# itzg's scripts handle moving to `/data/mods` or `/data/plugins` using `COPY_MODS_SRC` and `COPY_MODS_DEST` (etc)
#


#
# Server configs
#

debuglog "Copying /defaultconfigs-bindmount/server to $YC_CONFIGS_DIR"
run cp -r ${DEBUG:+-v} /defaultconfigs-bindmount/server/* $YC_CONFIGS_DIR

debuglog "Copying /serverconfig-bindmount to $YC_CONFIGS_DIR"
run cp -r ${DEBUG:+-v}  /serverconfig-bindmount/* $YC_CONFIGS_DIR

#
# Plugins
#

# Temporarily disable all plugin related staging dirs for usability concerns

# if [[ ${TYPE} == "BUKKIT" || ${TYPE} == "PAPER" ]]; then
#     debuglog ">> DETECTED BUKKIT/PAPER SERVER TYPE"

#     PLUGIN_CONFIGS_DIR="${YC_CONFIGS_DIR}plugins/"
#     if [[ ! -d $PLUGIN_CONFIGS_DIR ]]; then
#         mkdir $PLUGIN_CONFIGS_DIR
#     else
#         rm -rf ${PLUGIN_CONFIGS_DIR}/*
#     fi

#     debuglog "Copying /defaultconfigs-bindmount/plugins to ${PLUGIN_CONFIGS_DIR}"
#     run cp -r ${DEBUG:+-v} /defaultconfigs-bindmount/plugins/* $PLUGIN_CONFIGS_DIR

#     debuglog "Copying /pluginsconfig-bindmount to ${PLUGIN_CONFIGS_DIR}"
#     run cp -r ${DEBUG:+-v} /pluginsconfig-bindmount/* $PLUGIN_CONFIGS_DIR

#     PLUGINS_STAGING_DIR="/yc-plugins"
#     if [[ ! -d $PLUGINS_STAGING_DIR ]]; then
#         mkdir $PLUGINS_STAGING_DIR
#     else
#         rm -rf ${PLUGINS_STAGING_DIR}/*
#     fi

#     debuglog "Copying /defaultplugins-bindmount/ to ${PLUGINS_STAGING_DIR}"
#     run cp -r ${DEBUG:+-v} /defaultplugins-bindmount/* $PLUGINS_STAGING_DIR

#     debuglog "Copying /plugins-bindmount/ to ${PLUGINS_STAGING_DIR}"
#     run cp -r ${DEBUG:+-v} /plugins-bindmount/* $PLUGINS_STAGING_DIR
# fi

#
# Mod configs
#

if [[ ${TYPE} == "FORGE" || ${TYPE} == "FABRIC" ]]; then
    debuglog ">> DETECTED FORGE/FABRIC SERVER TYPE"

    MOD_CONFIGS_DIR="${YC_CONFIGS_DIR}config/"
    if [[ ! -d $MOD_CONFIGS_DIR ]]; then
        mkdir $MOD_CONFIGS_DIR
    else
        rm -rf ${MOD_CONFIGS_DIR}/*
    fi

    debuglog "Copying /defaultconfigs-bindmount/mods to ${MOD_CONFIGS_DIR}"
    run cp -r ${DEBUG:+-v} /defaultconfigs-bindmount/mods/* $MOD_CONFIGS_DIR

    debuglog "Copying /modsconfig-bindmount to ${MOD_CONFIGS_DIR}"
    run cp -r ${DEBUG:+-v} /modsconfig-bindmount/* $MOD_CONFIGS_DIR


    MODS_STAGING_DIR="/yc-mods"
    if [[ ! -d $MODS_STAGING_DIR ]]; then
        mkdir $MODS_STAGING_DIR
    else
        rm -rf ${MODS_STAGING_DIR}/*
    fi

    rm -rf ${MODS_STAGING_DIR}/*

    echo "Copying contents of /defaultmods-bindmount into ${MODS_STAGING_DIR}"
    cp -r ${DEBUG:+-v} /defaultmods-bindmount/* ${MODS_STAGING_DIR}/

    echo "Copying contents of /server-only-mods-bindmount into ${MODS_STAGING_DIR}"
    cp -r ${DEBUG:+-v} /server-only-mods-bindmount/* ${MODS_STAGING_DIR}/

    echo "Copying contents of /client-and-server-mods-bindmount into ${MODS_STAGING_DIR}"
    cp -r ${DEBUG:+-v} /client-and-server-mods-bindmount/* ${MODS_STAGING_DIR}/
fi