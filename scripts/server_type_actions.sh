
#
# There are two ServerTypeActions - this one and the yc-api one written in python.
# Conceptually, shellscript ServerTypeAction is performed every time on container startup.
#   meanwhile the python ServerTypeAction is called selectively, such as only on new env generation.
#
echo "Checking for any server type actions..."

# Forge type actions
if [[ ${TYPE} == "FORGE" || ${TYPE} == "FABRIC" ]]; then
    echo "Detected FORGE/FABRIC! Performing appropriate server type actions..."

    #
    # We technically could just move the mods into `/data/mods`, but since we're trying to explicitly
    # build on top of `itzg/minecraft` as a layer, we'll move things into `/yc-mods` and let
    # itzg's scripts handle moving to `/data/mods` using `COPY_MODS_SRC` and `COPY_MODS_DEST`
    #

    if [[ ! -d /yc-mods ]]; then
        mkdir /yc-mods
    fi

    rm -rf /yc-mods/*

    echo "Copying contents of /server-only-mods-bindmount into /yc-mods"
    cp -r /server-only-mods-bindmount/* /yc-mods/

    echo "Copying contents of /client-and-server-mods-bindmount into /yc-mods"
    cp -r /client-and-server-mods-bindmount/* /yc-mods/
fi