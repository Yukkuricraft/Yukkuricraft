import json
from pprint import pformat

from flask import Blueprint, request  # type: ignore
from datetime import datetime, timedelta
from docker.models.containers import Container

from src.api.lib.auth import (
    validate_access_token,
    intercept_cors_preflight,
    make_cors_response,
)
from src.api.lib.docker_management import (
    DockerManagement,
    convert_dockerpy_container_to_container_definition,
)
from src.api.lib.helpers import log_request, seconds_to_string

from src.common.environment import Env
from src.common.types import DataDirType
from src.common.logger_setup import logger

server_bp: Blueprint = Blueprint("server", __name__)

DockerMgmtApi = DockerManagement()


@server_bp.route("/<env_str>/containers", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def list_defined_containers_handler(env_str):
    """List all containers that are defined in the generated server compose for this env"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(DockerMgmtApi.list_defined_containers(Env(env_str)))

    return resp


@server_bp.route("/<env_str>/containers/active", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def list_active_containers_handler(env_str):
    """List all containers running"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    env = Env(env_str)
    containers = DockerMgmtApi.list_active_containers(env)

    resp.data = json.dumps(
        list(map(convert_dockerpy_container_to_container_definition, containers))
    )

    return resp


@server_bp.route("/<env_str>/containers/up", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def up_containers_handler(env_str):
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
def up_one_container_handler(env_str):
    resp = make_cors_response()
    container_name = request.json["container_name"]

    env = Env(env_str)
    resp_data = {}
    resp_data["success"] = DockerMgmtApi.up_one_container(container_name=container_name)
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<env_str>/containers/down", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def down_containers_handler(env_str):
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
def down_one_container_handler(env_str):
    env = Env(env_str)

    resp = make_cors_response()
    container_name = request.json["container_name"]

    resp_data = {}
    resp_data["success"] = DockerMgmtApi.down_one_container(
        container_name=container_name
    )
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<env_str>/containers/restart_one", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def restart_one_container_handler(env_str):
    env = Env(env_str)

    resp = make_cors_response()
    container_name = request.json["container_name"]

    resp_data = {}
    resp_data["success"] = DockerMgmtApi.restart_one_container(
        container_name=container_name
    )
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp
