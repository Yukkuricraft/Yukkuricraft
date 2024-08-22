FROM nginxproxy/nginx-proxy:alpine


# UID/GID are assumed to be 101 based on https://hub.docker.com/_/nginx
ENV UID=101
ENV GID=101

# Actual host docker gid should be passed in as a --build-arg
ARG DOCKER_GID=117

RUN if [ "$(cat /etc/group | grep :${DOCKER_GID}:)" = "" ]; then \
        addgroup --gid $DOCKER_GID docker; \
    else \
        echo "Group with GID ${DOCKER_GID} already exists - skipping groupadd"; \
    fi

# Copy custom nginx conf.d configs in
COPY --chown=$UID:$GID images/nginx-proxy/conf.d/ /etc/nginx/conf.d

RUN addgroup $(getent passwd $UID | cut -d: -f1) $(getent group $DOCKER_GID | cut -d: -f1)