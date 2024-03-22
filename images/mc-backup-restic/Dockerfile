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

RUN addgroup -g "$HOST_GID" hostuser
RUN adduser -S hostuser -u $HOST_UID -s /bin/bash hostuser

RUN mkdir /mysqldump && chown hostuser:hostuser /mysqldump

RUN chown -R hostuser:hostuser /backups
# Note, still running as root here. Need to chown restic dirs using custom entrypoint.
ENTRYPOINT ["/chown_restic_dir_then_entrypoint.sh"]