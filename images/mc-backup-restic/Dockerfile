FROM itzg/mc-backup:latest
COPY scripts/chown_restic_dir_then_entrypoint.sh /chown_restic_dir_then_entrypoint.sh
COPY scripts/restic.sh /restic.sh

# We're mashing two different images together and we want everything to run as the host uid/gid
USER root

RUN apk add --no-cache su-exec

ARG HOST_UID=1000
ARG HOST_GID=1000
ENV UID=$HOST_UID
ENV GID=$HOST_GID

# Because we sync GID's for both user/docker groups to the host fs, there's
# a possibility those GID ints are already taken. Check for such cases.
# (Eg, on Macs, /var/run/docker.sock is owned by 'staff' which is GID 20, which exists by default in debian.)
RUN if [ "$(cat /etc/group | grep :${HOST_GID}:)" = "" ]; then \
        addgroup --gid $HOST_GID hostuser; \
    else \
        echo "Group with GID ${HOST_GID} already exists - skipping groupadd"; \
    fi

RUN adduser -S hostuser -u $HOST_UID -s /bin/bash hostuser

RUN mkdir /mysqldump && chown ${HOST_UID}:${HOST_GID} /mysqldump

RUN chown -R ${HOST_UID}:${HOST_GID} /backups
# Note, still running as root here. Need to chown restic dirs using custom entrypoint.
ENTRYPOINT ["/chown_restic_dir_then_entrypoint.sh"]
