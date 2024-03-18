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
from src.common.helpers import log_exception

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

@backups_bp.route("/create-new-minecraft-backup", methods=["OPTIONS", "POST"])
@intercept_cors_preflight
@validate_access_token
@log_request
def create_new_minecraft_backup():
    """Creates a new ad-hoc minecraft backup"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    post_data = request.get_json()

    target_env = post_data.get("target_env", "")
    target_world_group = post_data.get("target_world_group", "")

    out = None
    success = False
    try:
        out = BackupsApi.backup_minecraft(Env(target_env), target_world_group)
        success = True
    except:
        log_exception(
            message="Failed to create backup!",
            data={
                "env": target_env,
                "world": target_world_group,
            },
        )

    resp.data = json.dumps({ "success": success, "output": out })
    return resp

@backups_bp.route("/restore-minecraft-backup", methods=["OPTIONS", "POST"])
@intercept_cors_preflight
@validate_access_token
@log_request
def restore_minecraft_backup():
    """Restores a minecraft backup"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    post_data = request.get_json()

    target_env = post_data.get("target_env", "")
    target_world_group = post_data.get("target_world_group", "")
    target_snapshot_id = post_data.get("target_snapshot_id", "")

    out = None
    success = False
    try:
        out = BackupsApi.restore_minecraft(Env(target_env), target_world_group, target_snapshot_id)
        success = True
    except:
        log_exception(
            message="Failed to restore backup!",
            data={
                "env": target_env,
                "world": target_world_group,
                "snapshot_id": target_snapshot_id,
            },
        )

    resp.data = json.dumps({ "success": success, "output": out })
    return resp