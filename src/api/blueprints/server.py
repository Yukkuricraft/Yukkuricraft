import io
import os
import pprint
import json
import codecs
import logging

logger = logging.getLogger(__name__)

from flask import Flask, Blueprint, request, abort

from pprint import pformat
from subprocess import check_output, Popen, PIPE
from typing import Optional, Dict, List, Tuple, Callable
from pathlib import Path


from src.api.lib.auth import (
    validate_access_token,
    intercept_cors_preflight,
    make_cors_response,
)
from src.api.lib.server_management import ServerManagement
from src.api.lib.environment import Env


server_bp: Blueprint = Blueprint("server", __name__)


ServerMgmtApi = ServerManagement()


@server_bp.route("/create-env", methods=["POST", "OPTIONS"])
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

    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    resp_data, new_env_name = ServerMgmtApi.create_new_env(
        proxy_port=proxy_port, env_alias=env_alias
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


@server_bp.route("/<env>", methods=["DELETE", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def delete_dev_env(env):
    env_dict = Env.from_env_string(env).toJson()

    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp_data = ServerMgmtApi.delete_dev_env(env=env)
    resp_data["env"] = env_dict

    resp.data = json.dumps(resp_data)
    return resp


@server_bp.route("/<env>/containers", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def list_defined_containers(env):
    """List all containers that are defined in the generated server compose for this env"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(ServerMgmtApi.list_defined_containers(env=env))

    return resp


@server_bp.route("/<env>/containers/active", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def list_active_containers(env):
    """List all containers running"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(ServerMgmtApi.list_active_containers(env=env))

    return resp


@server_bp.route("/<env>/containers/up", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def up_containers(env):
    resp = make_cors_response()
    resp_data = ServerMgmtApi.up_containers(env=env)
    resp_data["env"] = Env.from_env_string(env).toJson()

    resp.data = json.dumps(resp_data)
    return resp


@server_bp.route(
    "/<env>/containers/up_one/<container_name>", methods=["GET", "OPTIONS"]
)
@intercept_cors_preflight
@validate_access_token
def up_one_container(env, container_name):
    resp = make_cors_response()

    resp_data = ServerMgmtApi.up_one_container(env=env, container_name=container_name)
    resp_data["env"] = Env.from_env_string(env).toJson()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<env>/containers/down", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def down_containers(env):
    resp = make_cors_response()
    resp_data = ServerMgmtApi.down_containers(env=env)
    resp_data["env"] = Env.from_env_string(env).toJson()

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route(
    "/<env>/containers/down_one/<container_name>", methods=["GET", "OPTIONS"]
)
@intercept_cors_preflight
@validate_access_token
def down_one_container(env, container_name):
    resp = make_cors_response()

    resp_data = ServerMgmtApi.down_one_container(env=env, container_name=container_name)
    resp_data["env"] = Env.from_env_string(env).toJson()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp
