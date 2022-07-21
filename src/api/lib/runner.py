import os

from subprocess import Popen, PIPE
from typing import List, Optional, Dict, Tuple

from src.api.lib.environment import Environment
from src.common.logger_setup import logger


class Runner:
    @staticmethod
    def run(
        cmds: List[List[str]], env_vars: Optional[Dict[str, str]] = None
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

    @staticmethod
    @Environment.ensure_valid_env
    def run_make_cmd(cmd: List, env: str) -> Tuple[str, str]:
        env_vars = {"ENV": env}
        return Runner.run([cmd], env_vars=env_vars)
