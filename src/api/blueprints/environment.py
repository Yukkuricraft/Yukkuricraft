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
from src.api.lib.environment import list_valid_envs
from src.api.lib.runner import Runner

from src.common.logger_setup import logger

envs_bp: Blueprint = Blueprint("environment", __name__)


# TODO: Take args for velocity port
@envs_bp.route("/create-new-dev-env/<name>", methods=["OPTIONS", "POST"])
@intercept_cors_preflight
def create_new_dev_env(name: str):
    if request.method == "POST":
        resp = make_cors_response()
        resp.status = 200

        velocity_port = resp.data["velocity_port"]

        cmds = ["make", "create_new_env", name]

        resp.data = json.dumps(Runner.run_make_cmd(cmds))

        return resp


@envs_bp.route("/list-envs-with-configs", methods=["OPTIONS", "GET"])
@intercept_cors_preflight
def list_envs_with_configs():
    if request.method == "GET":
        resp = make_cors_response()
        resp.status = 200

        resp.data = json.dumps(list_valid_envs())

        return resp
