import os
import pprint

from subprocess import Popen, PIPE
from typing import List, Optional, Dict, Tuple

from src.common.logger_setup import logger
from src.common.decorators import serialize_tuple_out_as_dict


class Runner:
    @staticmethod
    @serialize_tuple_out_as_dict({"stdout": 0, "stderr": 1, "exit_code": 2})
    def run(
        cmds: List[List[str]], env_vars: Optional[Dict[str, str]] = None
    ) -> Tuple[str, str, int]:
        """
        run() can take multiple "sets" of commands and pass the stdout
        from one command to the stdin of the next. Hence, cmds is a List[List[str]]

        Eg,
        cmds = [
          ["cat", "foo.txt"],
          ["echo"],
        ]
        is equivalent to `cat foo.txt > echo`

        stderr is discarded as far as passing to the next stdin goes.
        """
        env = os.environ.copy()
        if env_vars is not None:
            for key, value in env_vars.items():
                env[key] = value

        prev_stdout, prev_stderr = "", ""

        for cmd in cmds:
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE, env=env)
            logger.info(f"Starting Popen proc (pid:{proc.pid}) - Running {pprint.pformat(cmd)}")
            stdout_b, stderr_b = proc.communicate(prev_stdout.encode("utf8"))

            prev_stdout, prev_stderr = stdout_b.decode("utf8"), stderr_b.decode("utf8")
            logger.info(f"Completed proc (pid:{proc.pid}) and got stdout/stderr")
            logger.warning(prev_stderr)

        return prev_stdout, prev_stderr, proc.returncode

    @staticmethod
    def run_make_cmd(cmd: List, env: str) -> Tuple[str, str, int]:
        env_vars = {"ENV": env}
        return Runner.run([cmd], env_vars=env_vars)
