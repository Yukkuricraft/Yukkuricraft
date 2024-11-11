#!/usr/bin/env python3

from http import HTTPStatus
import json

from flask import abort, request  # type: ignore
from flask_openapi3 import APIBlueprint  # type: ignore

from pprint import pformat

from src.api.blueprints import (
    CreateEnvironmentRequestBody,
    CreateEnvironmentResponse,
    DeleteEnvironmentResponse,
    EnvRequestPath,
    GenerateConfigsResponse,
    ListEnvironmentsResponse,
    UnauthorizedResponse,
)

from src.api import security
from src.api.lib.auth import (
    return_cors_response,
    validate_access_token,
    prepare_response,
)

from src.api.lib.environment import (
    list_valid_envs,
    create_new_env,
    delete_env,
    generate_env_configs,
)
from src.api.lib.helpers import log_request

from src.api.blueprints import environment_tag

from src.common.config import load_toml_config
from src.common.environment import Env
from src.common.logger_setup import logger
from src.common import server_paths

envs_bp: APIBlueprint = APIBlueprint(
    "environment",
    __name__,
    url_prefix="/environments",
    abp_security=security,
    abp_tags=[environment_tag],
    abp_responses={HTTPStatus.UNAUTHORIZED: UnauthorizedResponse},
)


@envs_bp.route("/create", methods=["OPTIONS"])
@log_request
def create_env_preflight_handler():
    return return_cors_response()


@envs_bp.post("/create", responses={HTTPStatus.OK: CreateEnvironmentResponse})
@validate_access_token
@log_request
def create_env_handler(body: CreateEnvironmentRequestBody):
    """Create a new environment"""

    proxy_port = body.PROXY_PORT
    if not proxy_port:
        abort(400)
    proxy_port = int(proxy_port)

    env_alias = body.ENV_ALIAS
    description = body.DESCRIPTION
    server_type = body.SERVER_TYPE
    enable_env_protection = body.ENABLE_ENV_PROTECTION

    resp = prepare_response()

    new_env: Env = create_new_env(
        proxy_port=proxy_port,
        env_alias=env_alias,
        enable_env_protection=enable_env_protection,
        server_type=server_type,
        description=description,
    )

    generate_env_configs(new_env)

    resp.data = json.dumps({"created_env": new_env.to_json()})

    logger.warning(resp)
    return resp


@envs_bp.route("/<string:env_str>", methods=["OPTIONS"])
@log_request
def delete_env_options_handler(env_str):
    return return_cors_response()


@envs_bp.delete(
    "/<string:env_str>",
    responses={
        HTTPStatus.OK: DeleteEnvironmentResponse,
        HTTPStatus.FORBIDDEN: UnauthorizedResponse,
    },
)
@validate_access_token
@log_request
def delete_env_handler(path: EnvRequestPath):
    """Delete environment"""
    env_str = path.env_str
    env = Env(env_str)

    env_config = load_toml_config(server_paths.get_env_toml_config_path(env.name))
    if env_config["general"].get("enable_env_protection", False):
        resp = prepare_response(status_code=403)
        resp.data = json.dumps(
            {
                "message": f"You can't delete an environment that has env protection enabled. Disable it before trying to delete {env}",
            }
        )
    elif env_str in ["env1"]:
        # Blegh. Hardcoding ugly.
        resp = prepare_response(status_code=403)
        resp.data = json.dumps(
            {
                "message": f"You can't delete env1/prod.",
            }
        )
    else:
        resp = prepare_response(status_code=200)

        resp_data = {}
        resp_data["success"] = delete_env(env_str)
        resp_data["env"] = env.to_json()

        logger.info(resp_data)

        resp.data = json.dumps(resp_data)

    return resp


@envs_bp.route("/<string:env_str>/generate/configs", methods=["OPTIONS"])
@log_request
def generate_configs_options_handler(env_str):
    return return_cors_response()


@envs_bp.post(
    "/<string:env_str>/generate/configs",
    responses={
        HTTPStatus.OK: GenerateConfigsResponse,
    },
)
@validate_access_token
@log_request
def generate_configs_handler(path: EnvRequestPath):
    """Generate configs for an environment"""
    env = Env(path.env_str)

    resp = prepare_response()
    resp_data = generate_env_configs(env)
    resp_data["env"] = env.to_json()

    resp.data = json.dumps(resp_data)
    return resp


@envs_bp.route("/list", methods=["OPTIONS"])
@log_request
def list_envs_with_configs_options_handler():
    return return_cors_response()


@envs_bp.get(
    "/list",
    responses={HTTPStatus.OK: ListEnvironmentsResponse},
)
@validate_access_token
@log_request
def list_envs_with_configs_handler():
    """List environments

    Returns any environment with a valid config
    """
    logger.info(pformat(request))
    resp = prepare_response()
    resp.status = 200

    valid_envs = list_valid_envs()
    valid_envs_as_dicts = list(map(lambda env: env.to_json(), valid_envs))

    resp.data = json.dumps({"envs": valid_envs_as_dicts})

    return resp
