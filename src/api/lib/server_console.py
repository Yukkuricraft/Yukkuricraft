import re
from typing import Generator
import docker  # type: ignore
import subprocess
import select
import time

from src.common.environment import Env
from src.common.logger_setup import logger
from sh import tail
from src.common.paths import ServerPaths
from src.common.types import DataFileType  # type: ignore


ansi_escape = re.compile(
    r"(?:\\x1b[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\\x1b\[|\\x9b)[0-?]*[ -/]*[@-~]|\\x[0-9a-z]{2}[=>]?|\\r)",
    re.VERBOSE,
)


def listen_to_server_console(env: Env, world_group_name: str) -> Generator:
    """
    "Why not use docker py or similar?"
    ANSI escape codes in minecraft logs. It's mainly a question of whether
    I want to deal with those (ie, strip them). I don't have a good answer on
    whether I want to disable color codes entirely (is disabling jline even still a thing?)
    Reading the log files directly like this at least skips the ANSI bs.

    Subject to change.
    """

    logger.info(">> ENTERING LISTEN_TO_SERVER_CONSOLE()")
    log_file = ServerPaths.get_data_files_path(env.name, world_group_name, DataFileType.LOG_FILES) / "latest.log"

    # Output N last lines of file
    for line in tail(log_file, "-n100"):
        yield line.strip()

    # "Tail" log file for any additional writes
    # TODO: Implement aborting loop
    with open(log_file, "r") as f:
        f.seek(0, 2)
        logger.info(f)
        while True:  # This needs to be reimplemented
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line.strip()
    logger.info("Returning")
    return
