import os
import json

from src.api.lib.environment import Environment
from typing import List, Optional, Dict, Tuple
from subprocess import Popen, PIPE

from src.common.logger_setup import logger


class ServerManagement:
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
        stdout, stderr = self.__run(cmds)

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

        stdout, stderr = self.__run_make_cmd(cmd, env=env)
        return stdout

    def down_containers(self, env: str):
        cmd = [
            "make",
            "down",
        ]

        stdout, stderr = self.__run_make_cmd(cmd, env=env)
        return stdout

    def up_one_container(self, env: str, container_name: str):
        cmd = [
            "make",
            "up_one",
            container_name,
        ]

        stdout, stderr = self.__run_make_cmd(cmd, env=env)
        return stdout

    def restart_containers(self, env: str):
        cmd = [
            "make",
            "restart",
        ]

        stdout, stderr = self.__run_make_cmd(cmd, env=env)
        return stdout

    def restart_one_container(self, env: str, container_name: str):
        cmd = [
            "make",
            "restart_one",
            container_name,
        ]

        stdout, stderr = self.__run_make_cmd(cmd, env=env)
        return stdout
