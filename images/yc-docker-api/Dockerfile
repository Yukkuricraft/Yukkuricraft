FROM python:3.10.5-buster
ENV PYTHONBUFFERED 1
ENV PYTHONPATH="/app:${PYTHONPATH}"


# Root stuff
RUN apt-get update && apt-get install --no-install-recommends --assume-yes \
    socat


# Non-root stuff
ARG UID=1000
ARG GID=1000
ARG DOCKER_GID=117
RUN groupadd --force --gid $DOCKER_GID docker \
    && groupadd --force --gid $GID yc-api \
    && useradd --uid $UID --gid yc-api --groups docker --shell /bin/bash --create-home yc-api

RUN mkdir /app
RUN chown -R yc-api:yc-api /app

COPY requirements.txt /app
RUN ls /app/*
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY --chown=yc-api:yc-api env/ /app/env
COPY --chown=yc-api:yc-api gen/ /app/gen
COPY --chown=yc-api:yc-api src/ /app/src
COPY --chown=yc-api:yc-api secrets/ /app/secrets

WORKDIR /app
USER yc-api
ENTRYPOINT ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "--log-file=-", "-w", "1", "-b", "0.0.0.0:5001", "src.api:create_app()", "--reload"]
