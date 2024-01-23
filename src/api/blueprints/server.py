import io
import os
import pprint
import json
import codecs
from flask import Flask, Blueprint, request, abort  # type: ignore

from pprint import pformat
from subprocess import check_output, Popen, PIPE
from typing import Optional, Dict, List, Tuple, Callable
from pathlib import Path

from src.api.lib.auth import (
    validate_access_token,
    intercept_cors_preflight,
    make_cors_response,
)
from src.api.lib.docker_management import DockerManagement
from src.common.environment import Env
from src.api.lib.helpers import log_request
from src.common.types import DataFileType
from src.common.logger_setup import logger

server_bp: Blueprint = Blueprint("server", __name__)

DockerMgmtApi = DockerManagement()


@server_bp.route("/<env_str>/containers", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def list_defined_containers(env_str):
    """List all containers that are defined in the generated server compose for this env"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(DockerMgmtApi.list_defined_containers(Env(env_str)))

    return resp


@server_bp.route("/<env_str>/containers/active", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def list_active_containers(env_str):
    """List all containers running"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(DockerMgmtApi.list_active_containers(Env(env_str)))

    return resp


@server_bp.route("/<env_str>/containers/up", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def up_containers(env_str):
    resp = make_cors_response()

    env = Env(env_str)
    resp_data = DockerMgmtApi.up_containers(env)
    resp_data["env"] = env.to_json()

    resp.data = json.dumps(resp_data)
    return resp


@server_bp.route("/<env_str>/containers/up_one", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def up_one_container(env_str):
    resp = make_cors_response()
    container_name = request.json["container_name"]

    env = Env(env_str)
    resp_data = DockerMgmtApi.up_one_container(env, container_name=container_name)
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<env_str>/containers/down", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def down_containers(env_str):
    env = Env(env_str)

    resp = make_cors_response()
    resp_data = DockerMgmtApi.down_containers(env)
    resp_data["env"] = env.to_json()

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<env_str>/containers/down_one", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def down_one_container(env_str):
    env = Env(env_str)

    resp = make_cors_response()
    container_name = request.json["container_name"]

    resp_data = DockerMgmtApi.down_one_container(env, container_name=container_name)
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route(
    "/containers/copy-configs-to-bindmount", methods=["OPTIONS", "POST"]
)
@intercept_cors_preflight
@validate_access_token
@log_request
def copy_configs_to_bindmount():
    if request.method == "POST":
        resp = make_cors_response()
        resp.status = 200

        container_name = request.json["container_name"]
        type = request.json["data_file_type"]

        data_file_type = DataFileType.from_str(type)
        output = DockerMgmtApi.copy_configs_to_bindmount(
            container_name, data_file_type
        )

        resp.data = json.dumps(output)
        return resp
