import io
import os
import pprint
import json
import codecs
import logging

logger = logging.getLogger(__name__)

from flask import Flask, Blueprint

from subprocess import check_output, Popen, PIPE
from typing import Optional, Dict, List, Tuple, Callable
from pathlib import Path


from src.api.lib.auth import (
    validate_access_token,
    intercept_cors_preflight,
    make_cors_response,
)
from src.api.lib.server_management import ServerManagement


docker_bp: Blueprint = Blueprint("docker", __name__)


ServerMgmtApi = ServerManagement()


@docker_bp.route("/<env>/containers", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def list_defined_containers(env):
    """List all containers that are defined in the generated docker compose for this env"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(ServerMgmtApi.list_defined_containers(env=env))

    return resp


@docker_bp.route("/<env>/containers/active", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def list_active_containers(env):
    """List all containers running"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(ServerMgmtApi.list_active_containers(env=env))

    return resp


@docker_bp.route("/<env>/containers/up", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def up_containers(env):
    resp = make_cors_response()
    resp.data = json.dumps(ServerMgmtApi.up(env=env))

    return resp


@docker_bp.route(
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


@docker_bp.route("/<env>/containers/down", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def down_containers(env):
    resp = make_cors_response()
    resp.data = json.dumps(ServerMgmtApi.down_containers(env=env))

    return resp


@docker_bp.route(
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
