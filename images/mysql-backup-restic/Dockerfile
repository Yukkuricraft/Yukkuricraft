FROM databack/mysql-backup:latest
COPY --from=instrumentisto/restic:latest /usr/local/bin/restic /usr/local/bin/restic

COPY scripts/copy_mysqldump_to_restic.sh /scripts.d/post-backup/copy_mysqldump_to_restic.sh
COPY scripts/chown_restic_dir_then_entrypoint.sh /chown_restic_dir_then_entrypoint.sh

# We're mashing two different images together and we want everything to run as the host uid/gid
USER root

RUN apk add --no-cache su-exec

ARG HOST_UID=1000
ARG HOST_GID=1000
ENV UID=$HOST_UID
ENV GID=$HOST_GID

RUN groupadd -g "$HOST_GID" hostuser
RUN useradd hostuser -u $HOST_UID -g $HOST_GID -m -s /bin/bash

RUN mkdir /mysqldump && chown hostuser:hostuser /mysqldump

RUN mkdir /backups
RUN chown -R hostuser:hostuser /backups

# Note, still running as root here. Need to chown restic dirs using custom entrypoint.
ENTRYPOINT ["/chown_restic_dir_then_entrypoint.sh"]