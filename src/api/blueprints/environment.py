#!/usr/bin/env python3

import json

from flask import Blueprint, abort, request

from pprint import pformat, pprint
from typing import Callable, Dict, Tuple

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
from src.api.lib.runner import Runner

from src.common.logger_setup import logger

envs_bp: Blueprint = Blueprint("environment", __name__)


@envs_bp.route("/create-env", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def create_env():
    """List all containers running"""
    post_data = request.get_json()

    proxy_port = post_data.get("PROXY_PORT", "")
    if not proxy_port:
        abort(400)
    proxy_port = int(proxy_port)

    env_alias = post_data.get("ENV_ALIAS", "")
    description = post_data.get("DESCRIPTION", "")

    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    resp_data, new_env_name = create_new_env(
        proxy_port=proxy_port,
        env_alias=env_alias,
        description=description,
    )
    logger.warning("????????????")
    logger.warning([resp_data, new_env_name])

    resp_data["created_env"] = {
        "env": Env.from_env_string(new_env_name).toJson(),
        "alias": env_alias,
        "port": proxy_port,
    }

    resp.data = json.dumps(resp_data)
    logger.warning(resp)
    return resp


@envs_bp.route("/<env>", methods=["DELETE", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def delete_env(env):
    env_dict = Env.from_env_string(env).toJson()

    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp_data = delete_dev_env(env=env)
    resp_data["env"] = env_dict

    resp.data = json.dumps(resp_data)
    return resp


@envs_bp.route("/list-envs-with-configs", methods=["OPTIONS", "GET"])
@intercept_cors_preflight
def list_envs_with_configs():
    if request.method == "GET":
        resp = make_cors_response()
        resp.status = 200

        valid_envs = list_valid_envs()
        valid_envs_as_dicts = list(map(lambda env: env.toJson(), valid_envs))

        resp.data = json.dumps(valid_envs_as_dicts)

        return resp
