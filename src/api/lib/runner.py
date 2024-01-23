import os
import pprint

from subprocess import Popen, PIPE
from typing import List, Optional, Dict, Tuple

from src.common.environment import Env

from src.common.logger_setup import logger
from src.common.decorators import serialize_tuple_out_as_dict
from src.common.runner import Runner as BaseRunner


class Runner(BaseRunner):
    @staticmethod
    def run_make_cmd(cmd: List, env: Env) -> Tuple[str, str, int]:
        """Wrapper for `Runner.run()` but adds the `env` as an env var

        Args:
            cmd (List): Make command to run. Eg, ["make", "up"]
            env (Env): Environment to run on

        Returns:
            Tuple[str, str, int]: Stdout, stdin, and return code
        """
        if not env:
            raise Exception("Must provide an env string!")

        env_vars = {"ENV": env.name}
        logger.info(env_vars)
        return Runner.run([cmd], env_vars=env_vars)
