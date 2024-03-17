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
from src.common.constants import YC_CONTAINER_NAME_LABEL

from src.common.environment import Env
from src.common.server_type_actions import ServerTypeActions
from src.common.types import DataFileType
from src.common.logger_setup import logger

server_bp: Blueprint = Blueprint("server", __name__)

DockerMgmtApi = DockerManagement()

# TODO: Figure out a better solution to this.
# Dockerpy gives us a robust and thorough Container object. However, we don't need 98% of that information
# on the frontend. We also have our old DTO models on the frontend side whose shape is not the same
# as dockerpy's Container object. Old shape is whatever `docker ps --format json` outputs.
# Basically if we want to have proper typing of the Container object on frontend, we'd have to extend our def
# to have _all_ of the dockerpy Container fields but that feels overkill.
# Instead, we'll just use this transformer function to convert dockerpy's Container back to our old ContainerDefinition shapes for now.
def convert_dockerpy_container_to_container_definition(container: Container):
    config = container.attrs.get("Config", {})
    state = container.attrs.get("State", {})
    labels = config.get("Labels", [])

    mounts = list(map(
        lambda d: f"{d['Source']}:{d['Destination']}",
        container.attrs.get("Mounts", [])
    ))
    hostname = config.get("Hostname", "unknown")
    names = [
        labels[YC_CONTAINER_NAME_LABEL],
        labels["com.docker.compose.service"],
        hostname,
    ]
    command = config.get("Cmd", None)
    entrypoint = config.get("Entrypoint", [])
    entry_command = command if command is not None else " ".join(entrypoint if entrypoint is not None else [])


    started_at = state.get("StartedAt", None)
    running_for = None
    status = None
    if started_at is None:
        running_for = "Container is down"
        status = "Container is down (unhealthy)"
    else:
        # datetime.datetime.fromisoformat() doesn't take `2024-02-11T22:16:57.510507768Z` as a format
        # which is what dockerpy gives us. 2024-02-11T22:16:57 is valid though so just drop the milliseconds.
        started_at_truncated_ms = started_at.split(".")[0]
        running_for_seconds = datetime.now() - datetime.fromisoformat(started_at_truncated_ms)
        running_for = seconds_to_string(running_for_seconds.total_seconds())

        health_status = state.get("Health", {}).get("Status", "unknown")
        status = f"Up {running_for} ({health_status})"
    return {
        "Command": entry_command,
        "ContainerName": hostname,
        "CreatedAt": container.attrs.get("Created", "unknown"),
        "Hostname": hostname,
        "ID": container.attrs.get("Id", "unknown"),
        "Image": config.get("Image", "unknown"),
        "Labels": labels,
        "Mounts": mounts,
        "Names": names,
        "Networks": list(config.get("NetworkSettings", {}).get("Networks", {}).keys()),
        "Ports": list(config.get("ExposedPorts", {}).keys()),
        "RunningFor": running_for,
        "State": state.get("Status", "unknown"),
        "Status": status,
    }

@server_bp.route("/<env_str>/containers", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def list_defined_containers(env_str):
    """List all containers that are defined in the generated server compose for this env"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")
    resp.data = json.dumps(DockerMgmtApi.list_defined_containers(Env(env_str)))

    return resp


@server_bp.route("/<env_str>/containers/active", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def list_active_containers(env_str):
    """List all containers running"""
    resp = make_cors_response()
    resp.headers.add("Content-Type", "application/json")

    env = Env(env_str)
    containers = DockerMgmtApi.list_active_containers(env)

    resp.data = json.dumps(list(map(convert_dockerpy_container_to_container_definition, containers)))

    return resp


@server_bp.route("/<env_str>/containers/up", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def up_containers(env_str):
    resp = make_cors_response()

    env = Env(env_str)
    resp_data = DockerMgmtApi.up_containers(env)
    resp_data["env"] = env.to_json()

    resp.data = json.dumps(resp_data)
    return resp


@server_bp.route("/<env_str>/containers/up_one", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def up_one_container(env_str):
    resp = make_cors_response()
    container_name = request.json["container_name"]

    env = Env(env_str)
    resp_data = {}
    resp_data["success"] = DockerMgmtApi.up_one_container(container_name=container_name)
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<env_str>/containers/down", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def down_containers(env_str):
    env = Env(env_str)

    resp = make_cors_response()
    resp_data = DockerMgmtApi.down_containers(env)
    resp_data["env"] = env.to_json()

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route("/<env_str>/containers/down_one", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def down_one_container(env_str):
    env = Env(env_str)

    resp = make_cors_response()
    container_name = request.json["container_name"]

    resp_data = {}
    resp_data["success"] = DockerMgmtApi.down_one_container(container_name=container_name)
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp

@server_bp.route("/<env_str>/containers/restart_one", methods=["POST", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
@log_request
def restart_one_container(env_str):
    env = Env(env_str)

    resp = make_cors_response()
    container_name = request.json["container_name"]

    ServerTypeActions().run(env)

    resp_data = {}
    resp_data["success"] = DockerMgmtApi.restart_one_container(container_name=container_name)
    resp_data["env"] = env.to_json()
    resp_data["container_name"] = container_name

    resp.data = json.dumps(resp_data)

    return resp


@server_bp.route(
    "/containers/copy-configs-to-bindmount", methods=["OPTIONS", "POST"]
)
@intercept_cors_preflight
@validate_access_token
@log_request
def copy_configs_to_bindmount():
    if request.method == "POST":
        resp = make_cors_response()
        resp.status = 200

        container_name = request.json["container_name"]
        type = request.json["data_file_type"]

        data_file_type = DataFileType.from_str(type)
        output = DockerMgmtApi.copy_configs_to_bindmount(
            container_name, data_file_type
        )

        resp.data = json.dumps(output)
        return resp