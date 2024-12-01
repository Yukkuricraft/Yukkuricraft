import os
import json
from datetime import datetime, timedelta, timezone
import docker
from docker.models.containers import Container
from docker import DockerClient, from_env
from concurrent.futures import ThreadPoolExecutor

from pprint import pformat
from typing import Any, Callable, List, Optional, Dict
from ptyprocess import PtyProcessUnicode  # type: ignore

from src.api.lib import LegacyActiveContainer, LegacyDefinedContainer
from src.api.lib.runner import Runner
from src.api.lib.helpers import InvalidContainerNameError, seconds_to_string
from src.common.config.config_node import ConfigNode
from src.common.environment import Env
from src.common.helpers import get_now_dt, log_exception
from src.common import server_paths
from src.common.logger_setup import logger
from src.common.config import load_yaml_config
from src.common.constants import (
    YC_CONTAINER_TYPE_LABEL,
    YC_ENV_LABEL,
    YC_CONTAINER_NAME_LABEL,
)


# TODO: Figure out a better solution to this.
# Dockerpy gives us a robust and thorough Container object. However, we don't need 98% of that information
# on the frontend. We also have our old DTO models on the frontend side whose shape is not the same
# as dockerpy's Container object. Old shape is whatever `docker ps --format json` outputs.
# Basically if we want to have proper typing of the Container object on frontend, we'd have to extend our def
# to have _all_ of the dockerpy Container fields but that feels overkill.
# Instead, we'll just use this transformer function to convert dockerpy's Container back to our old ContainerDefinition shapes for now.
def convert_dockerpy_container_to_legacy_active_container(
    container: Container,
) -> LegacyActiveContainer:
    config = container.attrs.get("Config", {})
    state = container.attrs.get("State", {})
    labels = config.get("Labels", {})

    logger.info(pformat(container))
    logger.info(pformat(container.attrs))
    logger.info(pformat(config))
    logger.info(pformat(state))
    logger.info(pformat(labels))

    mounts = list(
        map(
            lambda d: f"{d['Source']}:{d['Destination']}",
            container.attrs.get("Mounts", []),
        )
    )
    hostname = config.get("Hostname", "unknown")
    names = [
        labels[YC_CONTAINER_NAME_LABEL],
        labels["com.docker.compose.service"],
        hostname,
    ]
    command = config.get("Cmd", None)
    entrypoint = config.get("Entrypoint", [])
    entry_command = (
        command
        if command is not None
        else " ".join(entrypoint if entrypoint is not None else [])
    )

    started_at = state.get("StartedAt", None)
    running_for_str = None
    status = None
    if started_at is None:
        running_for_str = "Container is down"
        status = "Container is down (unhealthy)"
    else:
        # datetime.datetime.fromisoformat() doesn't take `2024-02-11T22:16:57.510507768Z` as a format
        # which is what dockerpy gives us. 2024-02-11T22:16:57 is valid though so just drop the milliseconds.

        started_at_truncated_ms = started_at.split(".")[0] + "Z"  # Add timezone back on

        try:
            running_for = get_now_dt() - datetime.fromisoformat(started_at_truncated_ms)
        except ValueError:
            running_for = timedelta(seconds=0)
        running_for_str = seconds_to_string(int(running_for.total_seconds()))

        health_status = state.get("Health", {}).get("Status", "unknown")
        status = f"Up {running_for_str} ({health_status})"
    return LegacyActiveContainer(
        **{
            "Command": entry_command,
            "ContainerName": hostname,
            "CreatedAt": container.attrs.get("Created", "unknown"),
            "Hostname": hostname,
            "ID": container.attrs.get("Id", "unknown"),
            "Image": config.get("Image", "unknown"),
            "Labels": labels,
            "Mounts": mounts,
            "Names": names,
            "Networks": list(
                config.get("NetworkSettings", {}).get("Networks", {}).keys()
            ),
            "Ports": list(config.get("ExposedPorts", {}).keys()),
            "RunningFor": running_for_str,
            "State": state.get("Status", "unknown"),
            "Status": status,
        }
    )


def convert_docker_compose_container_to_legacy_defined_container(
    svc_name: str, svc_data: ConfigNode, env: Env
) -> LegacyDefinedContainer:
    container = {}
    container["image"] = svc_data.get("image", "NO IMAGE")
    container["names"] = (
        [svc_name] if "name" not in svc_data else [svc_name, svc_data["name"]]
    )
    container["container_name"] = svc_data.get("container_name", "")
    container["hostname"] = svc_data.get("hostname", "")
    container["mounts"] = svc_data.get("mounts", [])
    container["networks"] = svc_data.get("networks", [])
    container["ports"] = svc_data.get("ports", [])

    labels = {}
    if "labels" in svc_data:
        for key, val in svc_data.labels.items():
            # TODO: Make this more robust. What else can be substituted?
            if val == "${ENV}":
                val = env.name
            labels[key] = val
    container["labels"] = labels

    return LegacyDefinedContainer(**container)


class DockerManagement:
    def __init__(self, client: Optional[DockerClient] = None):
        self.client = client if client else from_env()

    def pty_attach_container(self, container: Container):
        # This is super weird.
        # This only affects Paper/MC forks that use jline3
        # There's a bug between docker/jline3 where a docker ws attach causes jline3's persistent input line to not function.
        # "Not function" meaning the socket connection will send input correctly but doesn't send back the persistent input line modifications
        #   However, all input behaviors are still executed properly upon a `\n` being sent over the socket.
        # A CLI workaround was to call `docker attach` on each container that started. From a python script, calling `subprocess.Popen` with docker attach
        #   also worked. However, it only worked when executed from an interactive terminal ie was running inside a PTY. Thus, using `subprocess.Popen` from a
        #   server context with no PTY caused it to not work.
        # The final workaround that worked was to create a PTY process from the server using ptyprocess and run the `docker attach` inside of that.
        #
        # Wtf lol.
        if (
            YC_CONTAINER_TYPE_LABEL in container.labels
            and container.labels[YC_CONTAINER_TYPE_LABEL] == "minecraft"
        ):
            logger.info("Spawning process")
            p = PtyProcessUnicode.spawn(["docker", "attach", container.name])
            logger.info(f"Spawned. {pformat(p)}")
            try:
                logger.info("Is Alive?")
                logger.info(p.isalive())
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(lambda: p.read(1))
                    logger.info(future.result(timeout=1))
            except EOFError:
                logger.info("Got EOFError - Did not read from ptyprocess.")
            except TimeoutError:
                logger.info("Got TimeoutError - read() on PTY process failed!")
            except:
                log_exception()
            finally:
                logger.info("Done")

    def exec_run(
        self,
        container: Container,
        command: List[str],
        silent: bool = False,
        **extra_args,
    ):
        params = {
            "cmd": command,
            "demux": True,
        }

        if extra_args and type(extra_args) == dict:
            params.update(extra_args)

        exit_code, output = container.exec_run(**params)  # type: ignore
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
                log_exception(
                    message="Failed to decode byte string as utf8!",
                    data={"rtn_msg": rtn_msg},
                )

        return exit_code, rtn_msg.strip()

    def send_command_to_container(self, container_name: str, command: str):
        """Send a command to the minecraft console using rcon-cli

        Args:
            container_name (str): A docker container name or id
            command (str): Command string such as 'say hello', 'list', 'op remi_scarlet' etc

        Returns:
            str: Response from rcon-cli
        """

        return self.perform_cb_on_container(
            container_name=container_name,
            callback=lambda container: self.exec_run(container, ["rcon-cli", command])[
                1
            ],
        )

    def prepare_container_for_ws_attach(self, container_name: str):
        container = self.container_name_to_container(container_name)
        self.pty_attach_container(container)
        return True

    def container_name_to_container(self, container_name):
        return self.client.containers.get(container_name)

    def is_container_up(self, container_name: str) -> bool:
        """Checks if the `container_name` container is "up"

        Up is defined as:
        - Container exists
        - Container state is one of "running", "created", "restarting"

        Args:
            container_name (str): Container to check

        Returns:
            bool: True if container is up. False otherwise.
        """
        try:
            container = self.container_name_to_container(container_name)
            return container.status in ["running", "created", "restarting"]
        except docker.errors.NotFound:
            return False

    def list_defined_containers(self, env: Env) -> List[LegacyDefinedContainer]:
        """Since using `docker ps` only gives us active containers, we need to parse the list of "should be available" containers.

        We do this by parsing the generated `gen/docker-compose.{{ENV}}.yml` file.
        This may have unforseen bugs in the future...? :-/

        Args:
            env (str): Environment name string

        Returns:
            List[LegacyDefinedContainer]: List containing container definitions.
        """

        filepath = server_paths.get_generated_docker_compose_path(env.name)
        docker_compose = load_yaml_config(filepath, no_cache=True)

        logger.info(pformat(docker_compose))
        defined_containers: List = []
        for svc_name, svc_data in docker_compose.services.items():
            defined_containers.append(
                convert_docker_compose_container_to_legacy_defined_container(
                    svc_name, svc_data, env
                )
            )

        return defined_containers

    def list_active_containers(self, env: Env) -> List[Container]:
        """List containers for env that are currently up and running.

        Args:
            env (Env): Environment

        Returns:
            List[Container]: Container definitions as returned from `docker ps`
        """

        containers = self.client.containers.list(
            all=True, filters={"label": f"{YC_ENV_LABEL}={env.name}"}
        )

        return containers

    def perform_cb_on_container(
        self,
        container_name: str,
        callback: Callable[[Container], Any],
        additional_data_to_log: Optional[Dict] = None,
    ):
        """Wrapper for performing an action on a single dockerpy Container

        Args:
            container_name (str): A docker container name or id
            command (str): Command string such as 'say hello', 'list', 'op remi_scarlet' etc
            additional_data_to_log(Optional[Dict]): If an error is encountered, will include these in the data logged

        Returns:
            Optional[Any]: Return from the `callback` function, or None if cannot find container.
        """

        data = {
            "container_name": container_name,
        }
        if additional_data_to_log is not None:
            data.update(additional_data_to_log)

        container = None
        try:
            container = self.container_name_to_container(container_name)
            data["container"] = container
            logger.info(pformat(container.attrs))

            return callback(container)
        except docker.errors.NotFound:
            log_exception(
                message="Container could not be found! The env may be down if not an invalid name.",
                data=data,
            )
        except docker.errors.APIError:
            log_exception(message="Caught Docker API Error!", data=data)
        except InvalidContainerNameError:
            log_exception(
                message=f"Could not find a container by the name '{container_name}'!",
                data=data,
            )

        return None

    def up_one_container(self, container_name: str):
        """Start a single container by `container_name`

        If a container that's part of a docker compose config, the compose file must be running.
        Ie, the cluster that the container is in must be running.

        Args:
            container_name (str): A docker container name or id

        Returns:
            bool: True if successful
        """
        try:
            self.perform_cb_on_container(
                container_name=container_name,
                callback=lambda container: container.start(),
            )

            return True
        except:
            log_exception()

        return False

    def down_one_container(self, container_name: str):
        """Stop a single container by `container_name`

        If a container that's part of a docker compose config, the compose file must be running.
        Ie, the cluster that the container is in must be running.

        Args:
            container_name (str): A docker container name or id

        Returns:
            bool: True if successful
        """

        try:
            self.perform_cb_on_container(
                container_name=container_name,
                callback=lambda container: container.stop(),
            )
            return True
        except:
            log_exception()

        return False

    def restart_one_container(self, container_name: str):
        """Restart a single container by `container_name`

        If a container that's part of a docker compose config, the compose file must be running.
        Ie, the cluster that the container is in must be running.

        Args:
            container_name (str): A docker container name or id

        Returns:
            bool: True if successful
        """

        try:
            self.perform_cb_on_container(
                container_name=container_name,
                callback=lambda container: container.restart(),
            )
            return True
        except:
            log_exception()

        return False

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

    def up_containers(self, env: Env):
        """
        REFACTOR TO NOT USE MAKE

        TODO: When refactoring, ensure existence of all mount dirs and create+chown appropriately if not exists
        """

        cmd = [
            "make",
            "up",
        ]

        resp = Runner.run_make_cmd(cmd, env)

        return resp

    def down_containers(self, env: Env):
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "down",
        ]

        return Runner.run_make_cmd(cmd, env)

    def restart_containers(self, env: Env):
        """
        REFACTOR TO NOT USE MAKE
        """
        cmd = [
            "make",
            "restart",
        ]

        return Runner.run_make_cmd(cmd, env)
