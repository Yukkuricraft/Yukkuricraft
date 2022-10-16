FROM itzg/minecraft-server:java17 AS base

RUN mkdir /yc-worlds
RUN chown minecraft:minecraft /yc-worlds

COPY scripts/ /scripts
USER minecraft
RUN mkfifo /tmp/minecraft-console-in
ENTRYPOINT "/scripts/start.sh"
