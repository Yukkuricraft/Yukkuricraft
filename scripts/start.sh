#!/bin/bash

function debuglog {
    if [[ ! -z "$DEBUG" && ( "$DEBUG" == "1" || "$DEBUG" == "true" ) ]]; then echo $@; fi
}

function run {
    debuglog ">>>" $@
    $@
}

# Only chown entries that aren't already ${UID}:${GID}. A blanket `chown -R` rewrites every inode,
# which takes minutes on large trees like dynmap's tiles.
function chown_if_needed {
    if [[ ! -e "$1" ]]; then
        debuglog "Skipping chown of $1 - does not exist"
        return 0
    fi
    debuglog "Fixing ownership under $1 to ${UID}:${GID}"
    find "$1" \( ! -user "${UID}" -o ! -group "${GID}" \) -exec chown -h "${UID}:${GID}" {} +
}

# Maps symlink target -> symlink path
declare -A symlinkmap
function create_symlinks {
    debuglog "@@@@@@ ATTEMPTING TO CREATE SYMLINKS"
    local -n data=$1
    for src in "${!data[@]}"; do
        local dest="${data[$src]}"
        debuglog "${dest} -> ${src}"

        debuglog "Checking if symlink ${dest} exists already..."
        if [[ -L "${dest}" ]]; then
            debuglog "Symlink exists - deleting."
            rm "${dest}"
        fi

        debuglog "Ensuring symlink dest ${dest} isn't a regular dir/file..."
        if [[ -e "${dest}" ]]; then
            echo "WARNING: Not symlinking ${dest} -> ${src}: ${dest} already exists and isn't a symlink. Move its contents to ${src} and remove it."
            continue
        fi

        # Create the target and the symlink's parent dir if missing, owned by ${UID}:${GID}.
        # Only the dirs we create are chowned - never recurse into the target, which may be huge.
        local dir
        for dir in "${src}" "$(dirname "${dest}")"; do
            local missing=()
            while [[ ! -e "${dir}" ]]; do
                missing+=("${dir}")
                dir="$(dirname "${dir}")"
            done
            if (( ${#missing[@]} )); then
                debuglog "Creating ${missing[*]}"
                mkdir -p "${missing[0]}"
                chown "${UID}:${GID}" "${missing[@]}"
            fi
        done

        debuglog "Listing src"
        debuglog "$(ls -al "${src}")"

        debuglog "Symlinking ${src} to ${dest}"
        ln -s "${src}" "${dest}"
        chown -h "${UID}:${GID}" "${dest}"
    done
}

# START FLOW
debuglog "RUNNING AS: $(whoami)"
debuglog "MOTD: $MOTD"
debuglog "UID: $UID"
debuglog "GID: $GID"
debuglog "SERVER TYPE: $TYPE"

echo "################################################"
echo "STARTING CUSTOM YC/MINECRAFT-SERVER START SCRIPT"

# Load itzg/minecraft utils script
. /start-utils
echo "LOADED ITZG START-UTILS"

# run mkdir /data/logs
# run touch /data/logs/latest.log
run find /worlds-bindmount/ -name session.lock -type f -delete

# We use `bukkit.yml` to set the world path to the bindmount. If not bukkit/paper, we need to symlink.
# Atm we only deal with bukkit/paper and forge/fabric. Not sure about other server types.
if [[ ${TYPE} != "PAPER" && ${TYPE} != "BUKKIT" ]]; then
    symlinkmap["/worlds-bindmount"]="/data/world"
fi

# MISC_SYMLINKS is comma-separated `link:target` pairs, eg `/data/plugins/dynmap/web/tiles:/yc-misc/dynmap/tiles`
IFS=',' read -ra misc_symlinks <<< "${MISC_SYMLINKS:-}"
for pair in "${misc_symlinks[@]}"; do
    [[ -z "${pair}" ]] && continue
    symlinkmap["${pair#*:}"]="${pair%%:*}"
done

create_symlinks symlinkmap

# if [[ ${TYPE} == "PAPER" || ${TYPE} == "BUKKIT" ]]; then
#     # Clear out /data/plugins every time
#     args=(
#        --delete
#        --type file,directory
#        --min-depth=1 --max-depth "${REMOVE_OLD_MODS_DEPTH:-16}"
#        --name "${REMOVE_OLD_MODS_INCLUDE:-*}"
#        --exclude-name "${REMOVE_OLD_MODS_EXCLUDE:-}"
#     )
#     if ! isDebugging; then
#       args+=(--quiet)
#     fi
#     echo "DELETING ALL /data/plugins CONTENTS"
#     mc-image-helper find "${args[@]}" "/data/plugins"
# fi

# Merge all our "source" dirs into "staging" dirs
source /scripts/merge_data_files_into_yc_staging_dirs.sh

# Chowns
chown_if_needed /data
chown_if_needed /plugins-bindmount
chown_if_needed /worlds-bindmount
chown_if_needed /mods-bindmount
chown_if_needed /modsconfig-bindmount

echo "==============="
run ls -al /
run ls -al /data

echo "###########################################################"
echo "STARTING ORIGINAL ITZG/DOCKER-MINECRAFT-SERVER START SCRIPT"
echo $(whoami)

source /start