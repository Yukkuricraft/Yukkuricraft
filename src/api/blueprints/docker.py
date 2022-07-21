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
def list_containers(env):
    """List all containers running"""
    resp = make_cors_response()
    resp.data = json.dumps(ServerMgmtApi.list(env=env))

    return resp


@docker_bp.route("/<env>/containers/up", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def up_containers(env):
    """Spin up containers for <env>"""
    return ServerMgmtApi.up(env=env)


@docker_bp.route(
    "/<env>/containers/up_one/<container_name>", methods=["GET", "OPTIONS"]
)
@intercept_cors_preflight
@validate_access_token
def up_one_container(env, container_name):
    """Spin up one container(<>) for <env>"""
    return ServerMgmtApi.up_one(env, container_name)


@docker_bp.route("/<env>/containers/down", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def down_containers(env):
    """Spin down containers for <env>"""
    return ServerMgmtApi.down(env=env)


@docker_bp.route(
    "/<env>/containers/down_one/<container_name>", methods=["GET", "OPTIONS"]
)
@intercept_cors_preflight
@validate_access_token
def down_one_container(env, container_name):
    """Spin down one container(<>) for <env>"""
    return ServerMgmtApi.down_one(env, container_name)
