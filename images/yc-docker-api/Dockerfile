FROM python:3.10.5-buster

ENV PYTHONBUFFERED 1
ENV PYTHONPATH="/app:${PYTHONPATH}"

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends --assume-yes \
    socat

COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./env/ /app/env
COPY ./src/ /app/src

ENTRYPOINT ["python3", "src/api/main.py"]
