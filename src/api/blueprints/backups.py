import io
import os
import pprint
import json
import codecs

from flask import Flask, Blueprint, request, abort  # type: ignore
from datetime import datetime
from docker.models.containers import Container
from pprint import pformat
from subprocess import check_output, Popen, PIPE
from typing import Optional, Dict, List, Tuple, Callable
from pathlib import Path

from src.api.lib.auth import (
    validate_access_token,
    intercept_cors_preflight,
    make_cors_response,
)
from src.api.lib.backup_management import BackupManagement
from src.api.lib.docker_management import DockerManagement
from src.api.lib.helpers import log_request, seconds_to_string

from src.common.environment import Env
from src.common.types import DataFileType
from src.common.logger_setup import logger

backups_bp: Blueprint = Blueprint("backups", __name__)

BackupsApi = BackupManagement()


@backups_bp.route("/list-by-tags", methods=["OPTIONS", "POST"])
@intercept_cors_preflight
@validate_access_token
@log_request
def list_backups():
    """List all backups per tags"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    post_data = request.get_json()

    env_str = post_data.get("env_str", "")
    target_tags = post_data.get("target_tags", "")

    backups = BackupsApi.list_backups_by_env_and_tags(Env(env_str), target_tags)
    resp.data = json.dumps(backups)

    return resp
