import os
import json


from pprint import pformat
from typing import List, Optional, Dict, Tuple
from subprocess import Popen, PIPE

from src.api.lib.environment import ensure_valid_env
from src.api.lib.runner import Runner
from src.generator.docker_compose_gen import DockerComposeGen
from src.common.logger_setup import logger
from src.common.config import load_yaml_config
from src.common.decorators import serialize_tuple_out_as_dict


class ServerManagement:
    @ensure_valid_env
    def list_defined_containers(self, env: str):
        """
        Since using `docker ps` only gives us active containers, we need to parse the list of "should be available" containers.

        We do this by parsing the generated `gen/docker-compose.{{ENV}}.yml` file.
        This may have unforseen bugs in the future...? :-/
        """

        docker_compose_gen = DockerComposeGen(env)
        filepath = docker_compose_gen.get_generated_docker_compose_path()
        docker_compose = load_yaml_config(filepath)

        container_names = []
        for service in docker_compose["services"]:
            if "labels" in service:
                container_names.append(
                    service["labels"][docker_compose_gen.container_name_label]
                )

        return container_names

    @ensure_valid_env
    def list_active_containers(self, env: str):
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
                "--filter",
                f"label=net.yukkuricraft.env={env}",
            ],
        ]
        out = Runner.run(cmds)
        stdout, stderr, exit_code = out["stdout"], out["stderr"], out["exit_code"]

        containers: List[Dict] = []
        for line in stdout.splitlines():
            if len(line.strip()) == 0:
                continue
            container = json.loads(line)
            containers.append(container)

        return containers

    @ensure_valid_env
    def up_containers(self, env: str) -> Tuple[str, str, int]:
        cmd = [
            "make",
            "up",
        ]

        return Runner.run_make_cmd(cmd, env=env)

    @ensure_valid_env
    def down_containers(self, env: str) -> Tuple[str, str, int]:
        cmd = [
            "make",
            "down",
        ]

        return Runner.run_make_cmd(cmd, env=env)

    @ensure_valid_env
    def up_one_container(self, env: str, container_name: str) -> Tuple[str, str, int]:
        cmd = [
            "make",
            "up_one",
            container_name,
        ]

        return Runner.run_make_cmd(cmd, env=env)

    @ensure_valid_env
    def restart_containers(self, env: str) -> Tuple[str, str, int]:
        cmd = [
            "make",
            "restart",
        ]

        return Runner.run_make_cmd(cmd, env=env)

    @ensure_valid_env
    def restart_one_container(
        self, env: str, container_name: str
    ) -> Tuple[str, str, int]:
        cmd = [
            "make",
            "restart_one",
            container_name,
        ]

        return Runner.run_make_cmd(cmd, env=env)
