FROM postgres:16.0

# We'd be able to get away with the /etc/passwd mounting hack except it doesn't work on macs...
# To bypass the issue, actually create the host aligned UID/GID user via Dockerfile.

# Set up UID/GID
ARG HOST_UID=1000
ARG HOST_GID=1000
ENV UID=$HOST_UID
ENV GID=$HOST_GID

# Because we sync GID's for both user/docker groups to the host fs, there's
# a possibility those GID ints are already taken. Check for such cases.
# (Eg, on Macs, /var/run/docker.sock is owned by 'staff' which is GID 20, which exists by default in debian.)
RUN if [ "$(cat /etc/group | grep :${GID}:)" = "" ]; then \
        groupadd --force --gid $GID psql; \
    else \
        echo "Group with GID ${GID} already exists - skipping groupadd"; \
    fi

RUN useradd --uid $UID --gid $GID --shell /bin/bash --create-home psql