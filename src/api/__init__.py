from flask_openapi3 import OpenAPI, Info
from src.common import server_paths  # type: ignore

bearer_auth = {
    "type": "http",
    "scheme": "bearer",
}
security_schemes = {"bearerAuth": bearer_auth}
security = [{"bearerAuth": []}]

info = Info(title="Yukkuricraft Backend API", version="1.0.1")


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

    db_config = load_env_config(server_paths.get_api_db_env_file_path())
    app = OpenAPI("YC API", info=info, security_schemes=security_schemes)
    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"mysql://root:{db_config['MYSQL_ROOT_PASSWORD']}@yc-api-mysql/{db_config['MYSQL_DATABASE']}"

    app.register_api(auth_bp)
    app.register_api(backups_bp)
    app.register_api(envs_bp)
    app.register_api(files_bp)
    app.register_api(server_bp)
    app.register_api(sockets_bp)

    db.init_app(app)
    socketio.init_app(app)

    with app.app_context():
        db.create_all()

    return app
