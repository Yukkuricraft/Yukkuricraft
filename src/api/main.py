from flask import Flask
from flask_restx import Api, Resource, fields  # type: ignore

from src.api.docker import docker_blueprint

# Logging

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

logger.addHandler(ch)
logger.info("LOGGER INITIALIZED")


# Main

app = Flask("YC API")
app.register_blueprint(docker_blueprint, url_prefix="/docker")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
