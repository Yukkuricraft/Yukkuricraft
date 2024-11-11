#!/usr/bin/env python3

from http import HTTPStatus
import json

from flask import abort, request  # type: ignore
from flask_openapi3 import APIBlueprint  # type: ignore

from pathlib import Path

from src.api import security
from src.api.lib.auth import (
    return_cors_response,
    validate_access_token,
    prepare_response,
)
from src.api.lib.file_management import FileManager
from src.api.lib.helpers import log_request

from src.api.blueprints import (
    ListFilesRequestBody,
    ListFilesResponse,
    ReadFileRequestBody,
    ReadFileResponse,
    UnauthorizedResponse,
    WriteFileRequestBody,
    WriteFileResponse,
    files_tag,
)

from src.common.logger_setup import logger

files_bp: APIBlueprint = APIBlueprint(
    "files",
    __name__,
    url_prefix="/files",
    abp_security=security,
    abp_tags=[files_tag],
    abp_responses={HTTPStatus.UNAUTHORIZED: UnauthorizedResponse},
)


@files_bp.route("/list", methods=["OPTIONS"])
@log_request
def list_files_options_handler():
    return return_cors_response()


@files_bp.post(
    "/list",
    responses={HTTPStatus.OK: ListFilesResponse},
)
@validate_access_token
@log_request
def list_files_handler(body: ListFilesRequestBody):
    """List files"""
    path = body.PATH

    if not path:
        abort(400)
    path = Path(path)
    resp_data = FileManager.ls(path)

    resp = prepare_response()
    resp.data = json.dumps(resp_data)
    logger.info(resp.data)
    return resp


@files_bp.route("/read", methods=["OPTIONS"])
@log_request
def read_file_options_handler():
    return return_cors_response()


@files_bp.post(
    "/read",
    responses={HTTPStatus.OK: ReadFileResponse},
)
@validate_access_token
@log_request
def read_file_handler(body: ReadFileRequestBody):
    """Read file"""

    file_path = body.FILE_PATH
    if not file_path:
        abort(400)
    file_path = Path(file_path)
    resp_data = FileManager.read(file_path)

    resp = prepare_response()
    resp.data = json.dumps(resp_data)
    return resp


@files_bp.route("/write", methods=["OPTIONS"])
@log_request
def write_file_options_handler():
    return return_cors_response()


@files_bp.post(
    "/write",
    responses={HTTPStatus.OK: WriteFileResponse},
)
@validate_access_token
@log_request
def write_file_handler(body: WriteFileRequestBody):
    """Write file"""

    file_path = body.FILE_PATH
    if not file_path:
        abort(400)
    file_path = Path(file_path)

    content = body.CONTENT
    resp_data = FileManager.write(file_path, content)

    resp = prepare_response()
    resp.data = json.dumps(resp_data)
    return resp
