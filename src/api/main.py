from flask import Flask
from flask_restx import Api, Resource, fields  # type: ignore

import src.common.logger_setup
from src.common.config import load_env_config
from src.api.constants import DB_ENV_FILE
from src.api.docker import docker_bp
from src.api.auth import auth_bp
from src.api.db import db

db_config = load_env_config(DB_ENV_FILE)

app = Flask("YC API")
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"mysql://root:{db_config['MYSQL_ROOT_PASSWORD']}@yc-api-mysql/{db_config['MYSQL_DATABASE']}"

app.register_blueprint(docker_bp, url_prefix="/docker")
app.register_blueprint(auth_bp, url_prefix="/auth")

db.init_app(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
