FROM itzg/minecraft-server:java21-graalvm AS base
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

# ARG JMXREMOTE_CONFIG_PATH=/opt/java/openjdk/conf/management/
ARG JMXREMOTE_CONFIG_PATH=/usr/lib64/graalvm/graalvm-java21/conf/management

COPY secrets/jmxremote.password $JMXREMOTE_CONFIG_PATH/jmxremote.password
RUN chown $HOST_UID:$HOST_GID $JMXREMOTE_CONFIG_PATH/jmxremote.password && \
    chmod 600 $JMXREMOTE_CONFIG_PATH/jmxremote.password

COPY secrets/jmxremote.access $JMXREMOTE_CONFIG_PATH/jmxremote.access
RUN chown $HOST_UID:$HOST_GID $JMXREMOTE_CONFIG_PATH/jmxremote.access && \
    chmod 600 $JMXREMOTE_CONFIG_PATH/jmxremote.access

# Just in-case remotely SSH'ing in and dev'ing from vscode (windows) causes CRLF issues
RUN sed -i 's/\r$//' /scripts/start.sh && \
    chmod +x /scripts/start.sh

RUN mkfifo /tmp/minecraft-console-in
ENTRYPOINT [ "/scripts/start.sh" ]