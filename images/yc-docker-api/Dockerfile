FROM python:3.10.5-buster
ENV PYTHONBUFFERED 1
ENV PYTHONPATH="/app:${PYTHONPATH}"


# Install prereq packages
RUN apt-get update && apt-get install --no-install-recommends --assume-yes \
    socat ca-certificates curl gnupg

# Set up UID/GID - particularly for docker GID to match host docker GID
ARG UID=1000
ARG GID=1000
ARG DOCKER_GID=117
RUN groupadd --force --gid $DOCKER_GID docker \
    && groupadd --force --gid $GID yc-api \
    && useradd --uid $UID --gid yc-api --groups docker --shell /bin/bash --create-home yc-api

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
RUN chown -R yc-api:yc-api /app

COPY requirements.txt /app
RUN ls /app/*
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY --chown=yc-api:yc-api src/ /app/src
COPY --chown=yc-api:yc-api secrets/ /app/secrets
COPY --chown=yc-api:yc-api scripts/ /app/scripts
COPY --chown=yc-api:yc-api env/ /app/env
# COPY --chown=yc-api:yc-api gen/ /app/gen


# Eventually remove these 
COPY --chown=yc-api:yc-api Makefile /app
COPY --chown=yc-api:yc-api generate-docker-compose /app
COPY --chown=yc-api:yc-api generate-env-file /app
COPY --chown=yc-api:yc-api generate-new-dev-env /app
COPY --chown=yc-api:yc-api generate-velocity-config /app

WORKDIR /app
USER yc-api
ENTRYPOINT ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "--log-file=-", "-w", "1", "-b", "0.0.0.0:5001", "src.api:create_app()", "--reload"]
