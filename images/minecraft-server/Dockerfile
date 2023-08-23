FROM itzg/minecraft-server:java17 AS base
COPY scripts/ /scripts

ENV UID=1000
ENV GID=1000

# Create and set ownership of all mount endpoints
RUN mkdir /plugins-bindmount-prod
RUN mkdir /worlds-bindmount-prod
RUN mkdir /plugins-volume-dev
RUN mkdir /worlds-volume-dev

RUN chown $UID:$GID /plugins-bindmount-prod
RUN chown $UID:$GID /worlds-bindmount-prod
RUN chown $UID:$GID /plugins-volume-dev
RUN chown $UID:$GID /worlds-volume-dev

# Oh god this is confusing. We have to symlink this in the dockerfile
# cuz it's touching root. Can't symlink from start.sh cuz it's running as miencraft already.
RUN ln -s /worlds-bindmount-prod /yc-worlds

# Just in-case remotely SSH'ing in and dev'ing from vscode (windows) causes CRLF issues
RUN sed -i 's/\r$//' /scripts/start.sh  && \
    chmod +x /scripts/start.sh

USER minecraft
RUN mkfifo /tmp/minecraft-console-in
ENTRYPOINT "/scripts/start.sh"
