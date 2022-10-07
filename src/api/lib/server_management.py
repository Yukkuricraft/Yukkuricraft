import os
import json


from pprint import pformat
from typing import List, Optional, Dict, Tuple
from subprocess import Popen, PIPE

from src.api.constants import MIN_VALID_PROXY_PORT, MAX_VALID_PROXY_PORT
from src.api.lib.environment import ensure_valid_env, get_next_valid_dev_env_number
from src.api.lib.runner import Runner
from src.generator.docker_compose_gen import DockerComposeGen
from src.generator.generator import GeneratorType, get_generator
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

        defined_containers: List = []
        logger.info("+++++++++++ DEFINED CONTAINERS")
        logger.info(filepath)
        logger.info(repr(docker_compose.services))
        for svc_name, svc_data in docker_compose.services.items():
            container = {}
            container["image"] = svc_data.get_or_default("image", "NO IMAGE")
            container["names"] = (
                [svc_name] if "name" not in svc_data else [svc_name, svc_data["name"]]
            )
            container["mounts"] = svc_data.get_or_default("mounts", [])
            container["networks"] = svc_data.get_or_default("networks", [])
            container["ports"] = svc_data.get_or_default("ports", [])

            labels = []
            if "labels" in svc_data:
                for key, val in svc_data.labels.items():
                    # TODO: Make this more robust. What else can be substituted?
                    if val == "${ENV}":
                        val = env
                    labels.append(f"{key}={val}")
            container["labels"] = labels

            defined_containers.append(container)

        logger.warning("FOUND DEFINED CONTAINERS:")
        logger.warning(pformat(defined_containers))
        return defined_containers

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
