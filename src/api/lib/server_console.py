import re
from typing import Generator
import docker # type: ignore
import subprocess
import select
import time

from src.api.lib.environment import Env
from src.common.logger_setup import logger
from src.common.tail import follow
from sh import tail # type: ignore


ansi_escape = re.compile(r'(?:\\x1b[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\\x1b\[|\\x9b)[0-?]*[ -/]*[@-~]|\\x[0-9a-z]{2}[=>]?|\\r)', re.VERBOSE)

def listen_to_server_console(env: str, world_group_name: str) -> Generator:
  logger.info(">> ENTERING LISTEN_TO_SERVER_CONSOLE() (Nyan)")
  log_file = f"container_logs/{env}/worlds/{world_group_name}/latest.log"

  # Output N last lines of file
  for line in tail(log_file, "-n15"):
    yield line.strip()

  # "Tail" log file for any additional writes
  # TODO: Implement aborting loop
  with open(log_file, "r") as f:
    f.seek(0,2)
    logger.info(f);
    for _ in range(50): # tail -f's for ~5 seconds. This needs to be reimplemented
        line = f.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line.strip()
  logger.info("Returning")
  return