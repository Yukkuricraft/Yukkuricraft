FROM itzg/minecraft-server:java17 AS base
COPY scripts/ /scripts

ARG HOST_UID=1000
ARG HOST_GID=1000
ARG DOCKER_GID=117

RUN usermod -u $HOST_UID minecraft
RUN groupmod -o -g "$HOST_GID" minecraft
# Make docker group and add minecraft to it
RUN groupadd --force --gid $DOCKER_GID docker \
    && usermod -a -G docker minecraft

# Create and set ownership of all mount endpoints
RUN mkdir /plugins-bindmount-prod
RUN mkdir /worlds-bindmount-prod
RUN mkdir /plugins-volume-dev
RUN mkdir /worlds-volume-dev

RUN chown $HOST_UID:$HOST_GID /plugins-bindmount-prod
RUN chown $HOST_UID:$HOST_GID /worlds-bindmount-prod
RUN chown $HOST_UID:$HOST_GID /plugins-volume-dev
RUN chown $HOST_UID:$HOST_GID /worlds-volume-dev

# Oh god this is confusing. We have to symlink this in the dockerfile
# cuz it's touching root. Can't symlink from start.sh cuz it's running as miencraft already.
RUN ln -s /worlds-bindmount-prod /yc-worlds

# Just in-case remotely SSH'ing in and dev'ing from vscode (windows) causes CRLF issues
RUN sed -i 's/\r$//' /scripts/start.sh  && \
    chmod +x /scripts/start.sh

RUN mkfifo /tmp/minecraft-console-in
ENTRYPOINT "/scripts/start.sh"
