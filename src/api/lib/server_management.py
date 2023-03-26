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

class ServerManagement:
    """
    We should deprecate this class.

    This class acts as a holdover from the "Makefile days" where we ran all management commands through Makefile targets.
    We should port these methods to docker_management using native python code to execute our Docker related commands.

    New functionality should be written with python and not Makefiles.
    """

    @ensure_valid_env
    def up_containers(self, env: str) -> Tuple[str, str, int]:
        cmd = [
            "make",
            "up",
        ]

        return Runner.run([cmd], env_vars={ 'ENV': env, 'COPY_PROD_WORLD': '1', 'COPY_PROD_PLUGINS': '1' })

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
