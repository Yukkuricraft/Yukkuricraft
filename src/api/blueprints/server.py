import json
from flask import request  # type: ignore
from flask_openapi3 import APIBlueprint  # type: ignore

from pydantic import BaseModel, Field

from src.api.lib.auth import (
    return_cors_response,
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

server_bp: APIBlueprint = APIBlueprint("server", __name__, url_prefix="/server")
DockerMgmtApi = DockerManagement()

class EnvPath(BaseModel):
    env_str: str = Field(..., description="Environment id string")

@server_bp.route("/<string:env_str>/containers", methods=["OPTIONS"])
@log_request
def list_defined_containers_options_handler(env_str):
    return return_cors_response()


@server_bp.get("/<string:env_str>/containers")
@validate_access_token
@log_request
def list_defined_containers_handler(path: EnvPath):
    """List all containers that are defined in the generated server compose for this env"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(DockerMgmtApi.list_defined_containers(Env(path.env_str)))

    return resp


@server_bp.route("/<string:env_str>/containers/prepare_ws_attach", methods=["OPTIONS"])
@log_request
def prepare_ws_options_attach(path: EnvPath):
    return return_cors_response()


@server_bp.post("/<string:env_str>/containers/prepare_ws_attach")
@validate_access_token
@log_request
def prepare_ws_attach(path: EnvPath):
    """
    There's a bug where we need to `docker attach` from a PTY connected context in order for docker's websocket attach
    to work when using jline3.

    Yakumo will call this endpoint first to ensure whenever we try to attach to console, the container has been attached from
    the necessary PTY context to ensure it's ready.
    """
    resp = make_cors_response()
    container_name = request.json["container_name"]

    env = Env(path.env_path)
    resp_data = {}
    resp_data["success"] = DockerMgmtApi.prepare_container_for_ws_attach(
        container_name=container_name
    )
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<string:env_str>/containers/active", methods=["OPTIONS"])
@log_request
def list_active_containers_options_handler(env_str):
    return  return_cors_response()


@server_bp.get("/<string:env_str>/containers/active")
@validate_access_token
@log_request
def list_active_containers_handler(path: EnvPath):
    """List all containers running"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    env = Env(path.env_str)
    containers = DockerMgmtApi.list_active_containers(env)

    resp.data = json.dumps(
        list(map(convert_dockerpy_container_to_container_definition, containers))
    )

    return resp


@server_bp.route("/<string:env_str>/containers/up", methods=["OPTIONS"])
@log_request
def up_containers_options_handler(env_str):
    return return_cors_response()


@server_bp.post("/<string:env_str>/containers/up")
@validate_access_token
@log_request
def up_containers_handler(path: EnvPath):
    resp = make_cors_response()

    env = Env(path.env_str)
    resp_data = DockerMgmtApi.up_containers(env)
    resp_data["env"] = env.to_json()

    resp.data = json.dumps(resp_data)
    return resp


@server_bp.route("/<string:env_str>/containers/up_one", methods=["OPTIONS"])
@log_request
def up_one_container_options_handler(env_str):
    return return_cors_response()


@server_bp.post("/<string:env_str>/containers/up_one")
@validate_access_token
@log_request
def up_one_container_handler(path: EnvPath):
    resp = make_cors_response()
    container_name = request.json["container_name"]

    env = Env(path.env_str)
    resp_data = {}
    resp_data["success"] = DockerMgmtApi.up_one_container(container_name=container_name)
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<string:env_str>/containers/down", methods=["OPTIONS"])
@log_request
def down_containers_options_handler(env_str):
    return return_cors_response()


@server_bp.post("/<string:env_str>/containers/down")
@validate_access_token
@log_request
def down_containers_handler(path: EnvPath):
    env = Env(path.env_str)

    resp = make_cors_response()
    resp_data = DockerMgmtApi.down_containers(env)
    resp_data["env"] = env.to_json()

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<string:env_str>/containers/down_one", methods=["OPTIONS"])
@log_request
def down_one_container_options_handler(env_str):
    return return_cors_response()


@server_bp.post("/<string:env_str>/containers/down_one")
@validate_access_token
@log_request
def down_one_container_handler(path: EnvPath):
    env = Env(path.env_str)

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


@server_bp.route("/<string:env_str>/containers/restart_one", methods=["OPTIONS"])
@log_request
def restart_one_container_options_handler(env_str):
    return return_cors_response()


@server_bp.post("/<string:env_str>/containers/restart_one")
@validate_access_token
@log_request
def restart_one_container_handler(path: EnvPath):
    env = Env(path.env_str)

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
