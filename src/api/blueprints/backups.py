import json

from flask import Blueprint, request  # type: ignore

from src.api.lib.auth import (
    validate_access_token,
    intercept_cors_preflight,
    make_cors_response,
)
from src.api.lib.backup_management import BackupManagement
from src.api.lib.helpers import log_request

from src.common.environment import Env

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
