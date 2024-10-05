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
def list_backups_handler():
    """List all backups per tags"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    post_data = request.get_json()

    env_str = post_data.get("env_str", "")
    target_tags = post_data.get("target_tags", [])

    if type(target_tags) == str:
        target_tags = [target_tags]

    if type(target_tags) != list:
        raise ValueError(
            f"Got a value for 'target_tags' that we don't know how to parse! Got: '{resp(target_tags)}'"
        )

    target_tags.append(env_str)

    backups = BackupsApi.list_backups_by_env_and_tags(Env(env_str), target_tags)
    resp.data = json.dumps(backups)

    return resp


@backups_bp.route("/create-new-minecraft-backup", methods=["OPTIONS", "POST"])
@intercept_cors_preflight
@validate_access_token
@log_request
def create_new_minecraft_backup_handler():
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
    except Exception as e:
        log_exception(
            message="Failed to create backup!",
            data={
                "env": target_env,
                "world": target_world_group,
            },
        )
        out = type(e).__name__

    resp.data = json.dumps({"success": success, "output": out})
    return resp


@backups_bp.route("/restore-minecraft-backup", methods=["OPTIONS", "POST"])
@intercept_cors_preflight
@validate_access_token
@log_request
def restore_minecraft_backup_handler():
    """Restores a minecraft backup"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    post_data = request.get_json()

    target_hostname = post_data.get("target_hostname", "")
    target_snapshot_id = post_data.get("target_snapshot_id", "")

    target_env = None
    target_world_group = None
    if target_hostname:
        split = target_hostname.split("-")
        target_env, target_world_group = split[1], split[2]

    out = None
    success = False
    try:
        out = BackupsApi.restore_minecraft(
            Env(target_env), target_world_group, target_snapshot_id
        )
        success = True
    except Exception as e:
        log_exception(
            message="Failed to restore backup!",
            data={
                "env": target_env,
                "world": target_world_group,
                "snapshot_id": target_snapshot_id,
            },
        )
        out = type(e).__name__

    resp.data = json.dumps({"success": success, "output": out})
    return resp
