import json
import re
from flask import Flask
from flask_socketio import SocketIO

from pprint import pformat
from functools import total_ordering
from pathlib import Path
from typing import Any, Callable, List, Optional

from src.api.constants import CORS_ORIGIN, ENV_FOLDER, MIN_VALID_PROXY_PORT, MAX_VALID_PROXY_PORT
from src.api.lib.environment import Env
from src.common.config import load_toml_config
from src.common.logger_setup import logger
from src.generator.generator import GeneratorType, get_generator

socketio = SocketIO(cors_allowed_origins = [CORS_ORIGIN], logger=True, engineio_logger = True)

class ConsoleSocketMessage:
    env: Env
    worldgroup: str

    data: str