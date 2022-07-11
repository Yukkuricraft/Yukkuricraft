FROM python:3.10.5-buster

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends --assume-yes \
    socat

COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./env/ /app/env
COPY ./src/ /app/src
RUN ls /app

ENV PYTHONPATH="/app:${PYTHONPATH}"

ENTRYPOINT ["python3", "src/api/main.py"]
