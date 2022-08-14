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


server_bp: Blueprint = Blueprint("server", __name__)


ServerMgmtApi = ServerManagement()

# def create_new_env(self, env: str, proxy_port: int, env_alias: str = ""):
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
    resp.data = json.dumps(
        ServerMgmtApi.create_new_env(proxy_port=proxy_port, env_alias=env_alias)
    )

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
    resp.data = json.dumps(ServerMgmtApi.up_containers(env=env))

    return resp


@server_bp.route(
    "/<env>/containers/up_one/<container_name>", methods=["GET", "OPTIONS"]
)
@intercept_cors_preflight
@validate_access_token
def up_one_container(env, container_name):
    resp = make_cors_response()
    resp.data = json.dumps(
        ServerMgmtApi.up_one_container(env=env, container_name=container_name)
    )

    return resp


@server_bp.route("/<env>/containers/down", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def down_containers(env):
    resp = make_cors_response()
    resp.data = json.dumps(ServerMgmtApi.down_containers(env=env))

    return resp


@server_bp.route(
    "/<env>/containers/down_one/<container_name>", methods=["GET", "OPTIONS"]
)
@intercept_cors_preflight
@validate_access_token
def down_one_container(env, container_name):
    resp = make_cors_response()
    resp.data = json.dumps(
        ServerMgmtApi.down_one_container(env=env, container_name=container_name)
    )

    return resp
