from flask import Flask, Blueprint
from flask_restx import Api, Resource, fields  # type: ignore

from subprocess import check_output, Popen, PIPE
from typing import Optional, Dict, List, Tuple, Callable
from pathlib import Path

import io
import os
import pprint
import json
import codecs
import logging
logger = logging.getLogger(__name__)


docker_blueprint: Blueprint = Blueprint("docker", __name__)
docker_api: Api = Api(docker_blueprint)

# docker_api = api.namespace("docker", description="YC Docker Api")

Container = docker_api.model(
    "Container",
    {
        "Command": fields.String(required=True, description="Command"),
        "CreatedAt": fields.String(required=True, description="Created At"),
        "ID": fields.String(required=True, description="Container ID"),
        "Image": fields.String(required=True, description="Image Name"),
        "Labels": fields.String(required=True, description="Labels"),
        "LocalVolumes": fields.String(required=True, description="Local Volumes"),
        "Mounts": fields.String(required=True, description="Mounts"),
        "Names": fields.String(required=True, description="Names"),
        "Networks": fields.String(required=True, description="Networks"),
        "Ports": fields.String(required=True, description="Ports"),
        "RunningFor": fields.String(required=True, description="RunningFor"),
        "Size": fields.String(required=True, description="Size"),
        "State": fields.String(required=True, description="State"),
        "Status": fields.String(required=True, description="Status"),
    },
)


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


@docker_api.route("/")
class NotFound(Resource):

    @docker_api.doc("Not Found")
    def get(self):
        return ""


@docker_api.route("/<string:env>/containers")
@docker_api.param("env", "Environment to run the command on")
class ContainersList(Resource):

    @docker_api.doc("list_containers")
    @docker_api.marshal_list_with(Container)
    def get(self, env):
        """List all containers running"""
        return DockerApi.list(env=env)


@docker_api.route("/<string:env>/containers/up")
@docker_api.param("env", "Environment to run the command on")
class ContainersUp(Resource):
    @docker_api.doc("up_containers")
    def get(self, env):
        return DockerApi.up(env)


@docker_api.route("/<string:env>/containers/up_one/<string:container_name>")
@docker_api.param("env", "Environment to run the command on")
@docker_api.param("container_name", "Container name to run command on")
class ContainersUpOne(Resource):

    @docker_api.doc("up_container")
    def get(self, env: str, container_name: str):
        return DockerApi.up_one(env, container_name)


@docker_api.route("/<string:env>/containers/down")
@docker_api.param("env", "Environment to run the command on")
class ContainersDown(Resource):

    @docker_api.doc("down_containers")
    def get(self, env):
        return DockerApi.down(env)


@docker_api.route("/<string:env>/containers/restart_one/<string:container_name>")
@docker_api.param("env", "Environment to run the command on")
@docker_api.param("container_name", "Container name to run command on")
class ContainersRestartOne(Resource):

    @docker_api.doc("restart_container")
    def get(self, env: str, container_name: str):
        return DockerApi.restart_one(env, container_name)
