#!/usr/bin/env python3

import json

from flask import Blueprint, abort, request # type: ignore

from pprint import pformat, pprint
from typing import Callable, Dict, Tuple
from pathlib import Path

from src.api.constants import (
    ENV_FOLDER,
    YC_TOKEN_AUTH_SCHEME,
)
from src.api.lib.auth import (
    intercept_cors_preflight,
    validate_access_token,
    make_cors_response,
)
from src.api.db import db
from src.api.lib.environment import Env, list_valid_envs, create_new_env, delete_dev_env
from src.api.lib.file_management import FileManager
from src.api.lib.runner import Runner

from src.common.logger_setup import logger

files_bp: Blueprint = Blueprint("files", __name__)


@files_bp.route("/list", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def list_files():
    post_data = request.get_json()

    path = post_data.get("PATH", "")
    if not path:
        abort(400)
    path = Path(path)
    resp_data = FileManager.ls(path)

    resp = make_cors_response()
    resp.data = json.dumps(resp_data)
    logger.info(resp.data)
    return resp


@files_bp.route("/read", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def read_file():
    post_data = request.get_json()

    file_path = post_data.get("FILE_PATH", "")
    if not file_path:
        abort(400)
    file_path = Path(file_path)
    resp_data = FileManager.read(file_path)

    resp = make_cors_response()
    resp.data = json.dumps(resp_data)
    return resp

@files_bp.route("/write", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def write_file():
    post_data = request.get_json()

    file_path = post_data.get("FILE_PATH", "")
    if not file_path:
        abort(400)
    file_path = Path(file_path)
    content = post_data.get("CONTENT", "")
    resp_data = FileManager.write(file_path, content)

    resp = make_cors_response()
    resp.data = json.dumps(resp_data)
    return resp