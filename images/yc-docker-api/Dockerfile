FROM python:3.13
ENV PYTHONBUFFERED 1
ENV PYTHONPATH="/app:${PYTHONPATH}"


# Install prereq packages
RUN apt-get update && apt-get install --no-install-recommends --assume-yes \
    ca-certificates curl gnupg

# Set up UID/GID - particularly for docker GID to match host docker GID
ARG HOST_UID=1000
ARG HOST_GID=1000
ENV UID=$HOST_UID
ENV GID=$HOST_GID

ARG DOCKER_GID=117

# Because we sync GID's for both user/docker groups to the host fs, there's
# a possibility those GID ints are already taken. Check for such cases.
# (Eg, on Macs, /var/run/docker.sock is owned by 'staff' which is GID 20, which exists by default in debian.)
RUN if [ "$(cat /etc/group | grep :${GID}:)" = "" ]; then \
        groupadd --force --gid $GID yc-api; \
    else \
        echo "Group with GID ${GID} already exists - skipping groupadd"; \
    fi

RUN if [ "$(cat /etc/group | grep :${DOCKER_GID}:)" = "" ]; then \
        groupadd --force --gid $DOCKER_GID docker; \
    else \
        echo "Group with GID ${DOCKER_GID} already exists - skipping groupadd"; \
    fi

RUN useradd --uid $UID --gid $GID --groups $DOCKER_GID --shell /bin/bash --create-home yc-api

# Install docker binaries
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
RUN chmod a+r /etc/apt/keyrings/docker.gpg

RUN echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN apt-get update
RUN apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin --assume-yes

# Handle api files
RUN mkdir /app


COPY requirements.txt /app
RUN ls /app/*
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/src
COPY secrets/ /app/secrets
COPY scripts/ /app/scripts

RUN mkdir /app/env
RUN mkdir /app/gen


# Eventually remove these 
COPY Makefile /app
COPY generate-docker-compose /app
COPY generate-env-file /app
COPY generate-new-dev-env /app
COPY generate-velocity-config /app

RUN chown -R $UID:$GID /app

WORKDIR /app
USER yc-api
ENTRYPOINT ["gunicorn", "--worker-class", "gevent", "--log-file=-", "-w", "3", "-b", "0.0.0.0:5001", "src.api:create_app()", "--reload"]
