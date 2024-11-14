from http import HTTPStatus
import json
from pprint import pformat
from flask import request  # type: ignore
from flask_openapi3 import APIBlueprint  # type: ignore

from src.api import db, security
from src.api.lib.auth import (
    return_cors_response,
    validate_access_token,
    prepare_response,
)
from src.api.lib.docker_management import (
    DockerManagement,
    convert_dockerpy_container_to_container_definition,
)
from src.api.lib.helpers import log_request

from src.api.blueprints import (
    ContainerNameRequestPath,
    ListActiveContainersResponse,
    ListDefinedContainersResponse,
    UnauthorizedResponse,
    server_tag,
    EnvRequestPath,
)

from src.common.constants import YC_ENV_LABEL
from src.common.environment import Env
from src.common.logger_setup import logger

server_bp: APIBlueprint = APIBlueprint(
    "server",
    __name__,
    url_prefix="/server",
    abp_security=security,
    abp_tags=[server_tag],
    abp_responses={HTTPStatus.UNAUTHORIZED: UnauthorizedResponse},
)
DockerMgmtApi = DockerManagement()


def convert_container_name_to_env(container_name: str) -> Env:
    container = DockerMgmtApi.container_name_to_container(container_name)
    env_str = container.labels[YC_ENV_LABEL]
    return Env(env_str)


@server_bp.route("/cluster/<string:env_str>/defined", methods=["OPTIONS"])
@log_request
def list_defined_containers_options_handler(env_str):
    return return_cors_response()


@server_bp.get(
    "/cluster/<string:env_str>/defined",
    responses={
        HTTPStatus.OK: ListDefinedContainersResponse,
    },
)
@validate_access_token
@log_request
def list_defined_containers_handler(path: EnvRequestPath):
    """List defined containers

    List all containers that are defined in the generated docker compose for this env
    """
    resp = prepare_response()

    containers = DockerMgmtApi.list_defined_containers(Env(path.env_str))

    data = list(map(lambda container: container.model_dump(), containers))
    resp.data = json.dumps(
        {
            "defined_containers": data,
        }
    )
    resp.headers.add("Content-Type", "application/json")
    logger.info(resp.headers)

    return resp


@server_bp.route("/cluster/<string:env_str>/active", methods=["OPTIONS"])
@log_request
def list_active_containers_options_handler(env_str):
    return return_cors_response()


@server_bp.get(
    "/cluster/<string:env_str>/active",
    responses={
        HTTPStatus.OK: ListActiveContainersResponse,
    },
)
@validate_access_token
@log_request
def list_active_containers_handler(path: EnvRequestPath):
    """List running containers"""
    resp = prepare_response()

    env = Env(path.env_str)
    containers = DockerMgmtApi.list_active_containers(env)

    data = list(
        map(
            lambda c: convert_dockerpy_container_to_container_definition(
                c
            ).model_dump(),
            containers,
        )
    )
    resp.data = json.dumps(
        {
            "active_containers": data,
        }
    )

    return resp


@server_bp.route("/cluster/<string:env_str>/up", methods=["OPTIONS"])
@log_request
def up_containers_options_handler(env_str):
    return return_cors_response()


@server_bp.post("/cluster/<string:env_str>/up")
@validate_access_token
@log_request
def up_containers_handler(path: EnvRequestPath):
    """Start a cluster"""
    resp = prepare_response()

    env = Env(path.env_str)
    resp_data = DockerMgmtApi.up_containers(env)
    resp_data["env"] = env.to_json()

    resp.data = json.dumps(resp_data)
    return resp


@server_bp.route("/cluster/<string:env_str>/down", methods=["OPTIONS"])
@log_request
def down_containers_options_handler(env_str):
    return return_cors_response()


@server_bp.post("/cluster/<string:env_str>/down")
@validate_access_token
@log_request
def down_containers_handler(path: EnvRequestPath):
    """Shut down a cluster"""
    env = Env(path.env_str)

    resp = prepare_response()
    resp_data = DockerMgmtApi.down_containers(env)
    resp_data["env"] = env.to_json()

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route(
    "/container/<string:container_name>/prepare_ws_attach", methods=["OPTIONS"]
)
@log_request
def prepare_ws_options_attach(container_name):
    return return_cors_response()


@server_bp.post("/container/<string:container_name>/prepare_ws_attach")
@validate_access_token
@log_request
def prepare_ws_attach(path: ContainerNameRequestPath):
    """Prepares a container for websocket attach

    There's a bug where we need to `docker attach` from a PTY connected context in order for docker's websocket attach
    to work when using jline3.

    Yakumo will call this endpoint first to ensure whenever we try to attach to console, the container has been attached from
    the necessary PTY context to ensure it's ready.
    """
    resp = prepare_response()
    container_name = path.container_name

    resp_data = {}
    resp_data["success"] = DockerMgmtApi.prepare_container_for_ws_attach(
        container_name=container_name
    )
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/container/<string:container_name>/up", methods=["OPTIONS"])
@log_request
def up_one_container_options_handler(container_name):
    return return_cors_response()


@server_bp.post("/container/<string:container_name>/up")
@validate_access_token
@log_request
def up_one_container_handler(path: ContainerNameRequestPath):
    """Start a single container"""
    resp = prepare_response()
    container_name = path.container_name

    resp_data = {}
    resp_data["success"] = DockerMgmtApi.up_one_container(container_name=container_name)
    resp_data["container_name"] = container_name

    resp_data["env"] = convert_container_name_to_env(container_name).to_json()

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/container/<string:container_name>/down", methods=["OPTIONS"])
@log_request
def down_one_container_options_handler(container_name):
    return return_cors_response()


@server_bp.post("/container/<string:container_name>/down")
@validate_access_token
@log_request
def down_one_container_handler(path: ContainerNameRequestPath):
    """Shut down a single container"""
    resp = prepare_response()
    container_name = path.container_name

    resp_data = {}
    resp_data["success"] = DockerMgmtApi.down_one_container(
        container_name=container_name
    )
    resp_data["container_name"] = container_name
    resp_data["env"] = convert_container_name_to_env(container_name).to_json()

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/container/<string:container_name>/restart", methods=["OPTIONS"])
@log_request
def restart_one_container_options_handler(container_name):
    return return_cors_response()


@server_bp.post("/container/<string:container_name>/restart")
@validate_access_token
@log_request
def restart_one_container_handler(path: ContainerNameRequestPath):
    """Restart a single container"""
    resp = prepare_response()
    container_name = path.container_name

    resp_data = {}
    resp_data["success"] = DockerMgmtApi.restart_one_container(
        container_name=container_name
    )
    resp_data["container_name"] = container_name
    resp_data["env"] = convert_container_name_to_env(container_name).to_json()

    resp.data = json.dumps(resp_data)

    return resp
