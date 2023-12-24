import io
import os
import pprint
import json
import codecs
import logging

logger = logging.getLogger(__name__)

from flask import Flask, Blueprint, request, abort # type: ignore

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
from src.api.lib.docker_management import DockerManagement
from src.api.lib.environment import Env
from src.api.lib.types import ConfigType


server_bp: Blueprint = Blueprint("server", __name__)

ServerMgmtApi = ServerManagement()
DockerMgmtApi = DockerManagement()

@server_bp.route("/<env>/containers", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def list_defined_containers(env):
    """List all containers that are defined in the generated server compose for this env"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(DockerMgmtApi.list_defined_containers(env=env))

    return resp


@server_bp.route("/<env>/containers/active", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def list_active_containers(env):
    """List all containers running"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(DockerMgmtApi.list_active_containers(env=env))

    return resp


@server_bp.route("/<env>/containers/up", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def up_containers(env):
    resp = make_cors_response()
    resp_data = ServerMgmtApi.up_containers(env=env)
    resp_data["env"] = Env.from_env_string(env).toJson()

    resp.data = json.dumps(resp_data)
    return resp


@server_bp.route(
    "/<env>/containers/up_one", methods=["POST", "OPTIONS"]
)
@intercept_cors_preflight
@validate_access_token
def up_one_container(env):
    resp = make_cors_response()
    container_name = request.json['container_name']

    resp_data = ServerMgmtApi.up_one_container(env=env, container_name=container_name)
    resp_data["env"] = Env.from_env_string(env).toJson()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<env>/containers/down", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def down_containers(env):
    resp = make_cors_response()
    resp_data = ServerMgmtApi.down_containers(env=env)
    resp_data["env"] = Env.from_env_string(env).toJson()

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route(
    "/<env>/containers/down_one", methods=["POST", "OPTIONS"]
)
@intercept_cors_preflight
@validate_access_token
def down_one_container(env):
    resp = make_cors_response()
    container_name = request.json['container_name']

    resp_data = ServerMgmtApi.down_one_container(env=env, container_name=container_name)
    resp_data["env"] = Env.from_env_string(env).toJson()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp

@server_bp.route("/<env>/containers/copy-configs-to-bindmount", methods=["OPTIONS", "POST"])
@intercept_cors_preflight
@validate_access_token
def copy_configs_to_bindmount(env):
    if request.method == "POST":
        resp = make_cors_response()
        resp.status = 200

        container_name = request.json['container_name']
        type = request.json['config_type']

        config_type = ConfigType.from_str(type)
        output = DockerMgmtApi.copy_configs_to_bindmount(container_name, env, config_type)

        resp.data = json.dumps(output)
        return resp