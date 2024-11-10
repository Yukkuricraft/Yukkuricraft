#!/usr/bin/env python3

import json

from flask import abort, request  # type: ignore
from flask_openapi3 import APIBlueprint  # type: ignore

from pprint import pformat

from src.api.blueprints import EnvRequestPath

from src.api import security
from src.api.lib.auth import (
    return_cors_response,
    validate_access_token,
    make_cors_response,
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
    "environment", __name__, url_prefix="/environments", abp_security=security, abp_tags=[environment_tag]
)


@envs_bp.route("/create-env", methods=["OPTIONS"])
@log_request
def create_env_preflight_handler():
    return return_cors_response()


@envs_bp.post("/create-env")
@validate_access_token
@log_request
def create_env_handler():
    """List all containers running"""
    post_data = request.get_json()

    proxy_port = post_data.get("PROXY_PORT", "")
    if not proxy_port:
        abort(400)
    proxy_port = int(proxy_port)

    env_alias = post_data.get("ENV_ALIAS", "")
    description = post_data.get("DESCRIPTION", "")
    server_type = post_data.get("SERVER_TYPE", "")
    enable_env_protection = post_data.get("ENABLE_ENV_PROTECTION", False)

    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    resp_data = {}
    new_env: Env = create_new_env(
        proxy_port=proxy_port,
        env_alias=env_alias,
        enable_env_protection=enable_env_protection,
        server_type=server_type,
        description=description,
    )
    logger.warning("????????????")
    logger.warning([resp_data, new_env])

    generate_env_configs(new_env)

    resp_data["created_env"] = {
        "env": new_env.to_json(),
        "alias": env_alias,
        "port": proxy_port,
    }

    resp.data = json.dumps(resp_data)
    logger.warning(resp)
    return resp


@envs_bp.route("/<string:env_str>", methods=["OPTIONS"])
@log_request
def delete_env_options_handler(env_str):
    return return_cors_response()


@envs_bp.delete("/<string:env_str>")
@validate_access_token
@log_request
def delete_env_handler(path: EnvRequestPath):
    env_str = path.env_str
    env = Env(env_str)
    env_dict = env.to_json()

    env_config = load_toml_config(server_paths.get_env_toml_config_path(env.name))
    if env_config["general"].get("enable_env_protection", False):
        resp = make_cors_response(status_code=403)
        resp.headers.add("Content-Type", "application/json")
        resp.data = json.dumps(
            {
                "error": True,
                "message": f"You can't delete an environment that has env protection enabled. Disable it before trying to delete {env}",
            }
        )
    elif env_str in ["env1"]:
        # Blegh. Hardcoding ugly.
        resp = make_cors_response(status_code=403)
        resp.headers.add("Content-Type", "application/json")
        resp.data = json.dumps(
            {
                "error": True,
                "message": f"You can't delete env1/prod.",
            }
        )
    else:
        resp = make_cors_response(status_code=200)
        resp.headers.add("Content-Type", "application/json")

        resp_data = {}
        resp_data["success"] = delete_env(env_str)
        resp_data["env"] = env_dict

        logger.info(resp_data)

        resp.data = json.dumps(resp_data)

    return resp


@envs_bp.route("/<string:env_str>/generate-configs", methods=["OPTIONS"])
@log_request
def generate_configs_options_handler(env_str):
    return return_cors_response()


@envs_bp.post("/<string:env_str>/generate-configs")
@validate_access_token
@log_request
def generate_configs_handler(path: EnvRequestPath):
    env = Env(path.env_str)
    env_dict = env.to_json()

    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp_data = generate_env_configs(env)
    resp_data["env"] = env_dict

    resp.data = json.dumps(resp_data)
    return resp


@envs_bp.route("/list-envs-with-configs", methods=["OPTIONS"])
@log_request
def list_envs_with_configs_options_handler():
    logger.info("???")
    resp = return_cors_response()
    logger.info(pformat(resp))
    return resp


@envs_bp.get("/list-envs-with-configs")
@validate_access_token
@log_request
def list_envs_with_configs_handler():
    logger.info(pformat(request))
    resp = make_cors_response()
    resp.status = 200

    valid_envs = list_valid_envs()
    valid_envs_as_dicts = list(map(lambda env: env.to_json(), valid_envs))

    resp.data = json.dumps(valid_envs_as_dicts)

    return resp
