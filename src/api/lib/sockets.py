from flask_socketio import SocketIO  # type: ignore

from src.api.constants import (
    CORS_ORIGINS,
)
from src.common.environment import Env

socketio = SocketIO(
    cors_allowed_origins=CORS_ORIGINS,
    async_mode="gevent",
    logger=True,
    engineio_logger=True,
)


class ConsoleSocketMessage:
    env: Env
    worldgroup: str

    data: str
