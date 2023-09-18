#!/bin/bash

set -e

user=${HOSTUSER:-hostuser}

mount_path=${RESTIC_REPOSITORY}
mount_path_owner=$(ls -ld ${mount_path} | awk '{print $3}')
if [ "${user}" != "${mount_path_owner}" ]; then
  chown -R ${user}:${user} ${mount_path}
fi

echo exec su-exec ${user} ${ENTRYPOINT_TARGET}
exec su-exec ${user} ${ENTRYPOINT_TARGET}