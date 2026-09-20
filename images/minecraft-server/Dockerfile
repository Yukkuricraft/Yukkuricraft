ARG BASE_IMAGE=itzg/minecraft-server:java21-graalvm
FROM ${BASE_IMAGE} AS base
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

# Every itzg/minecraft-server variant sets JAVA_HOME, so this resolves for both the
# graalvm (/usr/lib64/graalvm/graalvm-javaNN) and openjdk (/opt/java/openjdk) bases.
# Don't hardcode it - a COPY to a wrong path silently creates it instead of failing.
COPY secrets/jmxremote.password $JAVA_HOME/conf/management/jmxremote.password
RUN chown $HOST_UID:$HOST_GID $JAVA_HOME/conf/management/jmxremote.password && \
    chmod 600 $JAVA_HOME/conf/management/jmxremote.password

COPY secrets/jmxremote.access $JAVA_HOME/conf/management/jmxremote.access
RUN chown $HOST_UID:$HOST_GID $JAVA_HOME/conf/management/jmxremote.access && \
    chmod 600 $JAVA_HOME/conf/management/jmxremote.access

# Just in-case remotely SSH'ing in and dev'ing from vscode (windows) causes CRLF issues
RUN sed -i 's/\r$//' /scripts/start.sh && \
    chmod +x /scripts/start.sh

RUN mkfifo /tmp/minecraft-console-in
ENTRYPOINT [ "/scripts/start.sh" ]