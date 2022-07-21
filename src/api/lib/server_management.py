import os
import json

from src.api.lib.environment import Environment
from typing import List, Optional, Dict, Tuple
from subprocess import Popen, PIPE

from src.api.lib.runner import Runner
from src.common.logger_setup import logger


class ServerManagement:
    @Environment.ensure_valid_env
    def list_containers(self, env: str):
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
        stdout, stderr = Runner.run(cmds)

        containers: List[Dict] = []
        for line in stdout.splitlines():
            container = json.loads(line)
            containers.append(container)

        return containers

    def up_containers(self, env: str):
        cmd = [
            "make",
            "up",
        ]

        stdout, stderr = Runner.run_make_cmd(cmd, env=env)
        return stdout

    def down_containers(self, env: str):
        cmd = [
            "make",
            "down",
        ]

        stdout, stderr = Runner.run_make_cmd(cmd, env=env)
        return stdout

    def up_one_container(self, env: str, container_name: str):
        cmd = [
            "make",
            "up_one",
            container_name,
        ]

        stdout, stderr = Runner.run_make_cmd(cmd, env=env)
        return stdout

    def restart_containers(self, env: str):
        cmd = [
            "make",
            "restart",
        ]

        stdout, stderr = Runner.run_make_cmd(cmd, env=env)
        return stdout

    def restart_one_container(self, env: str, container_name: str):
        cmd = [
            "make",
            "restart_one",
            container_name,
        ]

        stdout, stderr = Runner.run_make_cmd(cmd, env=env)
        return stdout
