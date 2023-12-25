import os
import json


from pprint import pformat
from typing import List, Optional, Dict, Tuple
from subprocess import Popen, PIPE

from src.api.constants import MIN_VALID_PROXY_PORT, MAX_VALID_PROXY_PORT
from src.api.lib.environment import ensure_valid_env
from src.api.lib.runner import Runner
from src.api.lib.types import ConfigType
from src.generator.docker_compose_gen import DockerComposeGen
from src.generator.generator import GeneratorType, get_generator
from src.common.logger_setup import logger
from src.common.config import load_yaml_config
from src.common.decorators import serialize_tuple_out_as_dict


class DockerManagement:
    @ensure_valid_env
    def list_defined_containers(self, env: str):
        """
        Since using `docker ps` only gives us active containers, we need to parse the list of "should be available" containers.

        We do this by parsing the generated `gen/docker-compose.{{ENV}}.yml` file.
        This may have unforseen bugs in the future...? :-/
        """

        docker_compose_gen = DockerComposeGen(env)
        filepath = docker_compose_gen.get_generated_docker_compose_path()
        docker_compose = load_yaml_config(filepath, no_cache=True)

        defined_containers: List = []
        for svc_name, svc_data in docker_compose.services.items():
            # logger.debug(pformat({"svc_name": svc_name, "svc_data": svc_data}))
            container = {}
            container["image"] = svc_data.get_or_default("image", "NO IMAGE")
            container["names"] = (
                [svc_name] if "name" not in svc_data else [svc_name, svc_data["name"]]
            )
            container["container_name"] = svc_data.get_or_default("container_name", "")
            container["hostname"] = svc_data.get_or_default("hostname", "")
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

    def send_command_to_container(self, container_name: str, command: str):
        cmds = [
            [
                "docker",
                "exec",
                container_name,
                "rcon-cli",
                command,
            ],
        ]

        out = Runner.run(cmds)
        stdout, stderr, exit_code = out["stdout"], out["stderr"], out["exit_code"]
        logger.info([stdout, stderr, exit_code])

        rtn_msg= stdout
        if stderr:
            rtn_msg += f"\n{stderr}"

        return rtn_msg.strip()

    def copy_configs_to_bindmount(self, container_name: str, env_str: str, type: ConfigType):
        if type == ConfigType.PLUGIN:
            # TODO Hardcoded paths :-/
            copy_src = "/data/plugins/*"
            copy_dest = "/yc-plugins"
        elif type == ConfigType.MOD:
            copy_src = "/data/config/*"
            copy_dest = "/modsconfig-bindmount"
        elif type == ConfigType.MOD_FILES:
            copy_src = "/data/mods"
            copy_dest = "/mods-bindmount"

        cmds = [
            [
                "docker",
                "exec",
                container_name,
                "bash",
                "-c",
                f"cp -r {copy_src} {copy_dest}"
            ]
        ]

        out = Runner.run(cmds)
        stdout, stderr, exit_code = out["stdout"], out["stderr"], out["exit_code"]
        logger.info([stdout, stderr, exit_code])

        rtn_msg= stdout
        if stderr:
            rtn_msg += f"\n{stderr}"

        return rtn_msg

    """
    ARGS=$(filter-out $@,$(MAKECMDGOALS))
    PRE=ENV=$(ENV)  COPY_PROD_WORLD=$(COPY_PROD_WORLD) COPY_PROD_PLUGINS=$(COPY_PROD_PLUGINS)
    COMPOSE_FILE="gen/docker-compose-$(ENV).yml"

    .PHONY: up
    up: generate
    up: __pre_ensure
    up:
        @if [[ -z "$(ENV)" ]]; then \
            echo 'Must pass ENV: make ENV=(prod|dev1) <target>. Aborting.'; \
            echo ''; \
            exit 1; \
        fi
        @if ! [[ "$(ENV)" =~ ^env$$ ]]; then \
            echo "ENV value must be 'env#' where # is any int. Got: $(ENV). Aborting."; \
            echo ''; \
            exit 1; \
        fi
        @if ! [[ -f "gen/$(ENV).env" ]]; then \
            echo "Got '$(ENV)' for ENV but could not find 'gen/$(ENV).env'! Was ./generate-env-file run first? Aborting."; \
            echo ''; \
            exit 1; \
        fi
        $(PRE) ./generate-velocity-config
        $(PRE) ./generate-env-file
        $(PRE) ./generate-docker-compose
        $(PRE) docker-compose -f "gen/docker-compose-$(ENV).yml" \
            --project-name $(ENV) \
            --project-directory $(shell pwd) \
            --env-file gen/$(ENV).env \
            up -d

    """

    @ensure_valid_env
    def up_containers(self, env: str) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "up",
        ]

        return Runner.run([cmd], env_vars={ 'ENV': env, 'COPY_PROD_WORLD': '1', 'COPY_PROD_PLUGINS': '1' })

    @ensure_valid_env
    def down_containers(self, env: str) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "down",
        ]

        return Runner.run_make_cmd(cmd, env=env)

    @ensure_valid_env
    def up_one_container(self, env: str, container_name: str) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "up_one",
            container_name,
        ]

        return Runner.run_make_cmd(cmd, env=env)

    @ensure_valid_env
    def restart_containers(self, env: str) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "restart",
        ]

        return Runner.run_make_cmd(cmd, env=env)

    @ensure_valid_env
    def restart_one_container(
        self, env: str, container_name: str
    ) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "restart_one",
            container_name,
        ]

        return Runner.run_make_cmd(cmd, env=env)

    def backup_container_volumes():
        pass
