from flask import Flask, Blueprint

from subprocess import check_output, Popen, PIPE
from typing import Optional, Dict, List, Tuple, Callable
from pathlib import Path

from src.api.auth import (
    validate_access_token,
    intercept_cors_preflight,
    make_cors_response,
)

import io
import os
import pprint
import json
import codecs
import logging

logger = logging.getLogger(__name__)


docker_bp: Blueprint = Blueprint("docker", __name__)


class Environment:
    env_folder: Path = Path("/app/env")

    @staticmethod
    def is_env_valid(env: str):
        env_file_path = Environment.env_folder / f"{env}.toml"
        return env_file_path.exists()

    @staticmethod
    def ensure_valid_env(func: Callable):
        """
        Decorated function must take a named arg called 'env'
        """

        def wrapper(*args, **kwargs):
            if "env" not in kwargs:
                raise Exception("Must pass an 'env' arg to this function call!")

            env = kwargs["env"]
            if not Environment.is_env_valid(env):
                raise Exception(
                    f"Tried to run a command on an environment that does not exist! Got: '{env}'"
                )
            return func(*args, **kwargs)

        return wrapper


class YCDockerApi:
    def __init__(self):
        pass

    def __run(
        self, cmds: List[List[str]], env_vars: Optional[Dict[str, str]] = None
    ) -> Tuple[str, str]:
        env = os.environ.copy()
        if env_vars is not None:
            for key, value in env_vars.items():
                env[key] = value

        prev_stdout, prev_stderr = "", ""

        for cmd in cmds:
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE, env=env)
            stdout_b, stderr_b = proc.communicate(prev_stdout.encode("utf8"))

            prev_stdout, prev_stderr = stdout_b.decode("utf8"), stderr_b.decode("utf8")
            logger.warning(prev_stderr)

        return prev_stdout, prev_stderr

    @Environment.ensure_valid_env
    def __run_make_cmd(self, cmd: List, env: str) -> Tuple[str, str]:
        env_vars = {"ENV": env}
        return self.__run([cmd], env_vars=env_vars)

    @Environment.ensure_valid_env
    def list(self, env: str):
        """
        Eh, the @Environment.ensure_valid_env decorator might be confusing
        as this func needs 'env=env' in the calling sig vs just 'env' for up/up_one/down/down_one
        """
        cmds = [
            [
                "docker",
                "ps",
                "-a",
                "--format",
                "{{ json . }}",
                "--no-trunc",
            ],
            ["grep", env],
        ]
        stdout, stderr = self.__run(cmds)

        containers = []
        for line in stdout.splitlines():
            container = json.loads(line)
            containers.append(container)

        return containers

    def up(self, env: str):
        cmd = [
            "make",
            "up",
        ]

        stdout, stderr = self.__run_make_cmd(cmd, env=env)
        return stdout

    def down(self, env: str):
        cmd = [
            "make",
            "down",
        ]

        stdout, stderr = self.__run_make_cmd(cmd, env=env)
        return stdout

    def up_one(self, env: str, container_name: str):
        cmd = [
            "make",
            "up_one",
            container_name,
        ]

        stdout, stderr = self.__run_make_cmd(cmd, env=env)
        return stdout

    def restart(self, env: str, container_name: str):
        cmd = [
            "make",
            "restart",
        ]

        stdout, stderr = self.__run_make_cmd(cmd, env=env)
        return stdout

    def restart_one(self, env: str, container_name: str):
        cmd = [
            "make",
            "restart_one",
            container_name,
        ]

        stdout, stderr = self.__run_make_cmd(cmd, env=env)
        return stdout


DockerApi = YCDockerApi()


@docker_bp.route("/<env>/containers", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def list_containers(env):
    """List all containers running"""
    resp = make_cors_response()
    resp.data = json.dumps(DockerApi.list(env=env))

    return resp


@docker_bp.route("/<env>/containers/up", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def up_containers(env):
    """Spin up containers for <env>"""
    return DockerApi.up(env=env)


@docker_bp.route(
    "/<env>/containers/up_one/<container_name>", methods=["GET", "OPTIONS"]
)
@intercept_cors_preflight
@validate_access_token
def up_one_container(env, container_name):
    """Spin up one container(<>) for <env>"""
    return DockerApi.up_one(env, container_name)


@docker_bp.route("/<env>/containers/down", methods=["GET", "OPTIONS"])
@intercept_cors_preflight
@validate_access_token
def down_containers(env):
    """Spin down containers for <env>"""
    return DockerApi.down(env=env)


@docker_bp.route(
    "/<env>/containers/down_one/<container_name>", methods=["GET", "OPTIONS"]
)
@intercept_cors_preflight
@validate_access_token
def down_one_container(env, container_name):
    """Spin down one container(<>) for <env>"""
    return DockerApi.down_one(env, container_name)
