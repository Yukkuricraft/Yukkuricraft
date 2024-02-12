import os
import json
import traceback
import docker
from docker.models.containers import Container

from pprint import pformat
from typing import List, Optional, Dict, Tuple
from subprocess import Popen, PIPE

from src.api.constants import MIN_VALID_PROXY_PORT, MAX_VALID_PROXY_PORT
from src.api.lib.runner import Runner
from src.common.environment import Env
from src.common.paths import ServerPaths
from src.common.logger_setup import logger
from src.common.config import load_yaml_config
from src.common.decorators import serialize_tuple_out_as_dict
from src.common.server_type_actions import ServerTypeActions
from src.common.types import DataFileType

class DockerManagement:
    def __init__(self):
        self.client = docker.from_env()

    def exec_run(self, container: Container, command: List[str], silent: bool = False, **extra_args):
        params = {
            "cmd": command,
            "demux": True,
        }

        if extra_args and type(extra_args) == dict:
            params.update(extra_args)

        exit_code, output = container.exec_run(**params)
        stdout, stderr = output

        rtn_msg = stdout
        if not silent:
            logger.info({"stdout": stdout})
        if stderr:
            if not silent:
                logger.info({"stderr": stderr})
            rtn_msg += f"\n{stderr}"

        if isinstance(rtn_msg, bytes):
            try:
                rtn_msg = rtn_msg.decode("utf-8")
            except:
                logger.warning("Failed to decode byte string as utf8!")
                logger.warning(rtn_msg)

        return exit_code, rtn_msg.strip()

    def container_name_to_container(self, container_name: str) -> Optional[Container]:
        try:
            container = self.client.containers.get(container_name)
            return container
        except docker.errors.NotFound:
            logger.error(f"Tried sending a command to container '{container_name}' but a container by that name did not exist!")
        except docker.errors.APIError:
            logger.error("Caught Docker API Error!")
            logger.error(traceback.format_exc())

        return None

    def list_defined_containers(self, env: Env) -> List[Dict]:
        """Since using `docker ps` only gives us active containers, we need to parse the list of "should be available" containers.

        We do this by parsing the generated `gen/docker-compose.{{ENV}}.yml` file.
        This may have unforseen bugs in the future...? :-/

        Args:
            env (str): Environment name string

        Returns:
            List[Dict]: List of dicts representing container definitions.
            TODO: Dataclass this.
        """

        filepath = ServerPaths.get_generated_docker_compose_path(env.name)
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

            labels = {}
            if "labels" in svc_data:
                for key, val in svc_data.labels.items():
                    # TODO: Make this more robust. What else can be substituted?
                    if val == "${ENV}":
                        val = env.name
                    labels[key] = val
            container["labels"] = labels

            defined_containers.append(container)

        return defined_containers

    def list_active_containers(self, env: Env) -> List[Container]:
        """List containers for env that are currently up and running.

        Args:
            env (Env): Environment

        Returns:
            List[Dict]: Container definitions as returned from `docker ps`
        """

        containers = self.client.containers.list(
            all=True,
            filters={
                "label": f"net.yukkuricraft.env={env.name}"
            }
        )

        return containers

    def send_command_to_container(self, container_name: str, command: str) -> str:
        """Send a command to the minecraft console using rcon-cli

        Args:
            container_name (str): A docker container name or id
            command (str): Command string such as 'say hello', 'list', 'op remi_scarlet' etc

        Returns:
            str: Response from rcon-cli
        """

        output = ""
        try:
            container = self.container_name_to_container(container_name)
            if container is None:
                return ""
            exit_code, output = self.exec_run(container, ["rcon-cli", command])
        except docker.errors.APIError:
            logger.error("Caught Docker API Error!")
            logger.error(traceback.format_exc())

        return output

    def copy_configs_to_bindmount(
        self, container_name: str, type: DataFileType
    ) -> str:
        """Copy `type` configs from the container back to the bindmounts, making them accessible on the host FS.

        Args:
            container_name (str): A docker container name or id
            env_str (str): Environment name string
            type (DataFileType): The type of configs to copy back.

        Returns:
            str: Verbose output from `cp -v`
        """
        if type == DataFileType.PLUGIN_CONFIGS:
            # TODO Hardcoded paths :-/
            copy_src = "/data/plugins/*"
            copy_dest = "/yc-plugins"
        elif type == DataFileType.MOD_CONFIGS:
            copy_src = "/data/config/*"
            copy_dest = "/modsconfig-bindmount"
        elif type == DataFileType.MOD_FILES:
            copy_src = "/data/mods"
            copy_dest = "/mods-bindmount"

        output = ""
        try:
            container = self.container_name_to_container(container_name)
            if container is None:
                return ""
            exit_code, output = self.exec_run(container, [
                "bash",
                "-c",
                f"cp -rv {copy_src} {copy_dest}"
            ])
        except docker.errors.APIError:
            logger.error("Caught Docker API Error!")
            logger.error(traceback.format_exc())

        return output

    """
    ARGS=$(filter-out $@,$(MAKECMDGOALS))
    PRE=ENV=$(ENV)
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

    def up_containers(self, env: Env) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """

        # Hack to use ServerTypeActions here. Should only be getting called from `environment.generate_env_configs()``
        ServerTypeActions().run(env)

        cmd = [
            "make",
            "up",
        ]

        return Runner.run_make_cmd(cmd, env)

    def down_containers(self, env: Env) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "down",
        ]

        return Runner.run_make_cmd(cmd, env)

    def up_one_container(self, env: Env, container_name: str) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "up_one",
            container_name,
        ]

        # Hack to use ServerTypeActions here. Should only be getting called from `environment.generate_env_configs()``
        ServerTypeActions().run(env)

        return Runner.run_make_cmd(cmd, env)

    def down_one_container(self, env: Env, container_name: str) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "up_one",
            container_name,
        ]

        return Runner.run_make_cmd(cmd, env)

    def restart_containers(self, env: Env) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "restart",
        ]

        # Hack to use ServerTypeActions here. Should only be getting called from `environment.generate_env_configs()``
        ServerTypeActions().run(env)

        return Runner.run_make_cmd(cmd, env)

    def restart_one_container(
        self, env: Env, container_name: str
    ) -> Tuple[str, str, int]:
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "restart_one",
            container_name,
        ]

        # Hack to use ServerTypeActions here. Should only be getting called from `environment.generate_env_configs()``
        ServerTypeActions().run(env)

        return Runner.run_make_cmd(cmd, env)
