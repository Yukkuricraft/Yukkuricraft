FROM python:3.10.5-buster

WORKDIR /app

COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./src/ /app/src

ENTRYPOINT ["python3", "src/api/main.py"]
