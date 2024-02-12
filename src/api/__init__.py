from flask import Flask
from src.common.paths import ServerPaths  # type: ignore


def create_app():
    from src.common.config import load_env_config
    from src.api.db import db
    from src.api.lib.sockets import socketio

    from src.api.blueprints.server import server_bp
    from src.api.blueprints.auth import auth_bp
    from src.api.blueprints.backups import backups_bp
    from src.api.blueprints.environment import envs_bp
    from src.api.blueprints.files import files_bp
    from src.api.blueprints.sockets import sockets_bp

    db_config = load_env_config(ServerPaths.get_db_env_file_path())
    app = Flask("YC API")
    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"mysql://root:{db_config['MYSQL_ROOT_PASSWORD']}@yc-api-mysql/{db_config['MYSQL_DATABASE']}"

    app.register_blueprint(server_bp, url_prefix="/server")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(backups_bp, url_prefix="/backups")
    app.register_blueprint(envs_bp, url_prefix="/environments")
    app.register_blueprint(files_bp, url_prefix="/files")
    app.register_blueprint(sockets_bp, url_prefix="/sockets")

    db.init_app(app)
    socketio.init_app(app)

    return app
