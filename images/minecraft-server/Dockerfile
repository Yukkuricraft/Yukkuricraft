FROM itzg/minecraft-server:java17 AS base
COPY scripts/ /scripts

ARG HOST_UID=1000
ARG HOST_GID=1000
ARG DOCKER_GID=117

ENV UID=$HOST_UID
ENV GID=$HOST_GID

RUN usermod -u $HOST_UID minecraft
RUN groupmod -o -g "$HOST_GID" minecraft
# Make docker group and add minecraft to it
RUN groupadd --force --gid $DOCKER_GID docker \
    && usermod -a -G docker minecraft

# Create and set ownership of all mount endpoints
RUN mkdir /plugins-bindmount
RUN mkdir /worlds-bindmount

RUN chown $HOST_UID:$HOST_GID /plugins-bindmount
RUN chown $HOST_UID:$HOST_GID /worlds-bindmount

# Just in-case remotely SSH'ing in and dev'ing from vscode (windows) causes CRLF issues
RUN sed -i 's/\r$//' /scripts/start.sh  && \
    chmod +x /scripts/start.sh

RUN mkfifo /tmp/minecraft-console-in
ENTRYPOINT [ "/scripts/start.sh" ]
