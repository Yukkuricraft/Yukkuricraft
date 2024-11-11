from flask_openapi3 import APIBlueprint  # type: ignore
from flask_socketio import emit  # type: ignore

from src.api import security
from src.api.lib.sockets import socketio
from src.api.lib.docker_management import DockerManagement

from src.api.blueprints import sockets_tag

from src.common.logger_setup import logger
from src.common.environment import Env

from src.api.lib.helpers import log_request

DockerMgmtApi = DockerManagement()
sockets_bp: APIBlueprint = APIBlueprint(
    "sockets",
    __name__,
    url_prefix="/sockets",
    abp_security=security,
    abp_tags=[sockets_tag],
)


@socketio.on("connect")
@log_request
def connect_handler(*args, **kwargs):
    logger.info("CLIENT CONNECTED")
    logger.info(args)
    logger.info(kwargs)


@socketio.on("disconnect")
@log_request
def disconnect_handler(*args, **kwargs):
    logger.info("CLIENT disconnectED")
    logger.info(args)
    logger.info(kwargs)


@socketio.on("message")
@log_request
def get_socket_message_handler(msg):
    logger.info("SOCKET GOT MESSAGE0")
    logger.info(msg)
    emit("event", "remilia scarlet")


@socketio.on("*")
@log_request
def catch_all(event, data):
    logger.info("UNCAUGHT SOCKET EVENT")
    logger.info(event)
    logger.info(data)
