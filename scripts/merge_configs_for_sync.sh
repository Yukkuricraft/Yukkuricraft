#!/usr/bin/env bash

function debuglog {
    if [[ ! -z "$DEBUG" && ( "$DEBUG" == "1" || "$DEBUG" == "true" ) ]]; then echo $@; fi
}

function run {
    debuglog ">>>" $@
    $@
}

if [[ ! -d "/yc-configs" ]]; then
    mkdir /yc-configs/
fi

#
# Server configs
#

debuglog "Copying /defaultconfigs-bindmount/server to /yc-configs"
run cp -rv /defaultconfigs-bindmount/server/* /yc-configs/

debuglog "Copying /serverconfig-bindmount to /yc-configs"
run cp -rv  /serverconfig-bindmount/* /yc-configs/

#
# Plugin configs
#

if [[ ${TYPE} == "BUKKIT" || ${TYPE} == "PAPER" ]]; then
    if [[ ! -d "/yc-configs/plugins" ]]; then
        mkdir /yc-configs/plugins/
    fi

    debuglog "Copying /defaultconfigs-bindmount/plugins to /yc-configs"
    run cp -rv /defaultconfigs-bindmount/plugins/* /yc-configs/plugins/

    debuglog "Copying /pluginsconfig-bindmount to /yc-configs"
    run cp -rv  /pluginsconfig-bindmount/* /yc-configs/plugins/
fi

#
# Mod configs
#

if [[ ${TYPE} == "FORGE" || ${TYPE} == "FABRIC" ]]; then
    if [[ ! -d "/yc-configs/config" ]]; then
        mkdir /yc-configs/config/
    fi

    debuglog "Copying /defaultconfigs-bindmount/mods to /yc-configs"
    run cp -rv /defaultconfigs-bindmount/mods/* /yc-configs/config/

    debuglog "Copying /modsconfig-bindmount to /yc-configs/config/"
    run cp -rv /modsconfig-bindmount/* /yc-configs/config/
fi