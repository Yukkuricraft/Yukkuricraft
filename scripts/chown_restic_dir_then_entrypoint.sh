#!/bin/bash

set -e

host_uid=${HOST_UID:-NO_HOST_UID}
host_gid=${HOST_GID:-NO_HOST_GID}
username=$(cat /etc/passwd | grep :${host_uid}: | cut -d\: -f1)

echo "host_uid: $host_uid"
echo "host_gid: $host_gid"
echo "username: $username"

mount_path=${RESTIC_REPOSITORY}
mount_path_owner=$(ls -ld ${mount_path} | awk '{print $3}')
if [ "${username}" != "${mount_path_owner}" ]; then
  chown -R ${uid}:${gid} ${mount_path}
fi

echo exec su-exec ${username} ${ENTRYPOINT_TARGET}
exec su-exec ${username} ${ENTRYPOINT_TARGET}