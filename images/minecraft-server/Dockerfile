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

COPY secrets/jmxremote.password /opt/java/openjdk/conf/management/jmxremote.password
RUN chown $HOST_UID:$HOST_GID /opt/java/openjdk/conf/management/jmxremote.password && \
    chmod 600 /opt/java/openjdk/conf/management/jmxremote.password

COPY secrets/jmxremote.access /opt/java/openjdk/conf/management/jmxremote.access
RUN chown $HOST_UID:$HOST_GID /opt/java/openjdk/conf/management/jmxremote.access && \
    chmod 600 /opt/java/openjdk/conf/management/jmxremote.access

# Just in-case remotely SSH'ing in and dev'ing from vscode (windows) causes CRLF issues
RUN sed -i 's/\r$//' /scripts/start.sh && \
    chmod +x /scripts/start.sh

RUN mkfifo /tmp/minecraft-console-in
ENTRYPOINT [ "/scripts/start.sh" ]