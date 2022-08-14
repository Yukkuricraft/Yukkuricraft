from flask import Flask

import src.common.logger_setup
from src.common.config import load_env_config
from src.api.constants import DB_ENV_FILE
from src.api.db import db

from src.api.blueprints.server import server_bp
from src.api.blueprints.auth import auth_bp
from src.api.blueprints.environment import envs_bp

db_config = load_env_config(DB_ENV_FILE)

app = Flask("YC API")
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"mysql://root:{db_config['MYSQL_ROOT_PASSWORD']}@yc-api-mysql/{db_config['MYSQL_DATABASE']}"

app.register_blueprint(server_bp, url_prefix="/server")
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(envs_bp, url_prefix="/environments")

db.init_app(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
