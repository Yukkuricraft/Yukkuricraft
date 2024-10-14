import json
from flask import Blueprint, request  # type: ignore

from src.api.lib.auth import (
    validate_access_token,
    intercept_cors_preflight,
    make_cors_response,
)
from src.api.lib.docker_management import (
    DockerManagement,
    convert_dockerpy_container_to_container_definition,
)
from src.api.lib.helpers import log_request
from src.common.environment import Env

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

@server_bp.route("/<env_str>/containers/prepare_ws_attach", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def up_one_container_handler(env_str):
    """
    There's a bug where we need to `docker attach` from a PTY connected context in order for docker's websocket attach
    to work when using jline3.

    Yakumo will call this endpoint first to ensure whenever we try to attach to console, the container has been attached from
    the necessary PTY context to ensure it's ready.
    """
    resp = make_cors_response()
    container_name = request.json["container_name"]

    env = Env(env_str)
    resp_data = {}
    resp_data["success"] = DockerMgmtApi.prepare_container_for_ws_attach(container_name=container_name)
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

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
