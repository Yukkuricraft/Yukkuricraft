from flask import Blueprint
from flask_socketio import emit

from src.api.lib.sockets import socketio
from src.api.lib.server_console import listen_to_server_console
from src.common.logger_setup import logger

sockets_bp = Blueprint('sockets', __name__)

@socketio.on('connect')
def connect(*args, **kwargs):
    logger.info("CLIENT CONNECTED")
    logger.info(args)
    logger.info(kwargs)

@socketio.on('connect to console')
def connect_to_console(msg):
    logger.info("SOCKET GOT CONSOLE CONNECT REQUEST")
    logger.info(msg)
    logger.info(list(listen_to_server_console(None, 'YC-lobby-prod')))
    for item in listen_to_server_console(None, "YC-lobby-prod"):
        logger.info(item)
        emit('log from console', item)
    emit('log from console', '0123456789'*25)

@socketio.on('poop')
def get_socket_poop(msg):
    logger.info("SOCKET GOT POOP")
    logger.info(msg)
    emit('event', 'scarlet reimi')

@socketio.on('message')
def get_socket_message(msg):
    logger.info("SOCKET GOT MESSAGE0")
    logger.info(msg)
    emit('event', 'remilia scarlet')

@socketio.on('message1')
def get_socket_message1(msg):
    logger.info("SOCKET GOT MESSAGE1")
    logger.info(msg)
    emit('event', 'scarlet remilia')

@socketio.on('message2')
def get_socket_message2(msg):
    logger.info("SOCKET GOT MESSAGE2")
    logger.info(msg)
    emit('event', 'reimi scarlet')

@socketio.on("*")
def catch_all(event, data):
    logger.info("UNCAUGHT SOCKET EVENT")
    logger.info(event)
    logger.info(data)
