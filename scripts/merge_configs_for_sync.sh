#!/usr/bin/env bash

function debuglog {
    if [[ ! -z "$DEBUG" && ( "$DEBUG" == "1" || "$DEBUG" == "true" ) ]]; then echo $@; fi
}

function run {
    debuglog ">>>" $@
    $@
}

# Copy configs
if [[ ! -d "/yc-configs" ]]; then
    mkdir /yc-configs/
fi

debuglog "Copying /defaultconfigs-server-bindmount to /yc-configs"
run cp -rv /defaultconfigs-server-bindmount/* /yc-configs/

debuglog "Copying /serverconfig-bindmount to /yc-configs"
run cp -rv  /serverconfig-bindmount/* /yc-configs/

if [[ ! -d "/yc-configs/plugins" ]]; then
  mkdir /yc-configs/plugins/
fi
debuglog "Copying /pluginsconfig-bindmount to /yc-configs"
run cp -rv  /pluginsconfig-bindmount/* /yc-configs/plugins/

if [[ ${TYPE} == "FORGE" || ${TYPE} == "FABRIC" ]]; then
    if [[ ! -d "/yc-configs/config" ]]; then
        mkdir /yc-configs/config/
    fi

    debuglog "Copying /modsconfig-bindmount to /yc-configs/config/"
    run cp -rv /modsconfig-bindmount/* /yc-configs/config/
fi