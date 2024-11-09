#!/usr/bin/env python3

import json

from flask import abort, request  # type: ignore
from flask_openapi3 import APIBlueprint  # type: ignore

from pathlib import Path

from src.api.lib.auth import (
    intercept_cors_preflight,
    return_cors_response,
    validate_access_token,
    make_cors_response,
)
from src.api.lib.file_management import FileManager
from src.api.lib.helpers import log_request

from src.common.logger_setup import logger

files_bp: APIBlueprint = APIBlueprint("files", __name__, url_prefix="/files")


@files_bp.route("/list", methods=["OPTIONS"])
@log_request
def list_files_options_handler():
    return return_cors_response()


@files_bp.post("/list")
@validate_access_token
@log_request
def list_files_handler():
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


@files_bp.route("/read", methods=["OPTIONS"])
@log_request
def read_file_options_handler():
    return return_cors_response()


@files_bp.post("/read")
@validate_access_token
@log_request
def read_file_handler():
    post_data = request.get_json()

    file_path = post_data.get("FILE_PATH", "")
    if not file_path:
        abort(400)
    file_path = Path(file_path)
    resp_data = FileManager.read(file_path)

    resp = make_cors_response()
    resp.data = json.dumps(resp_data)
    return resp


@files_bp.route("/write", methods=["OPTIONS"])
@log_request
def write_file_options_handler():
    return return_cors_response()


@files_bp.post("/write")
@validate_access_token
@log_request
def write_file_handler():
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
