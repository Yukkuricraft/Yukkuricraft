from flask import Blueprint  # type: ignore
from flask_socketio import emit  # type: ignore

from src.api.lib.sockets import socketio
from src.api.lib.server_console import listen_to_server_console
from src.api.lib.docker_management import DockerManagement
from src.common.logger_setup import logger
from src.api.lib.helpers import log_request

DockerMgmtApi = DockerManagement()

sockets_bp = Blueprint("sockets", __name__)


@socketio.on("connect")
@log_request
def connect(*args, **kwargs):
    logger.info("CLIENT CONNECTED")
    logger.info(args)
    logger.info(kwargs)


@socketio.on("disconnect")
@log_request
def disconnect(*args, **kwargs):
    logger.info("CLIENT disconnectED")
    logger.info(args)
    logger.info(kwargs)


@socketio.on("connect to console")
@log_request
def connect_to_console(data):
    env, world_group_name = data.get("env", None), data.get("world_group_name", None)
    logger.info("SOCKET GOT CONSOLE CONNECT REQUEST")
    logger.info(data)
    for item in listen_to_server_console(env, world_group_name):
        logger.info(f"#> {item}")
        emit("log from console", item)
    # emit('log from console', '0123456789'*25)


@socketio.on("exec server command")
@log_request
def exec_server_command(data):
    container_name, command = data.get("container_name", None), data.get(
        "command", None
    )

    if container_name is None or command is None:
        raise ValueError(
            f"Got no value for one or more arguments: container_name='{container_name}', command='{command}'"
        )

    logger.info(
        f"EXECUTING COMMAND ON SERVER CONTAINER: container_name='{container_name}' - cmd='{command}'"
    )
    message = DockerMgmtApi.send_command_to_container(container_name, command)
    emit("log from console", message)


@socketio.on("poop")
@log_request
def get_socket_poop(msg):
    logger.info("SOCKET GOT POOP")
    logger.info(msg)
    emit("event", "scarlet reimi")


@socketio.on("message")
@log_request
def get_socket_message(msg):
    logger.info("SOCKET GOT MESSAGE0")
    logger.info(msg)
    emit("event", "remilia scarlet")


@socketio.on("message1")
@log_request
def get_socket_message1(msg):
    logger.info("SOCKET GOT MESSAGE1")
    logger.info(msg)
    emit("event", "scarlet remilia")


@socketio.on("message2")
@log_request
def get_socket_message2(msg):
    logger.info("SOCKET GOT MESSAGE2")
    logger.info(msg)
    emit("event", "reimi scarlet")


@socketio.on("*")
@log_request
def catch_all(event, data):
    logger.info("UNCAUGHT SOCKET EVENT")
    logger.info(event)
    logger.info(data)
