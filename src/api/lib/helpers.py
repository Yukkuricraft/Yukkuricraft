import os
import re
import pwd
import docker
from docker.models.containers import Container

from typing import Callable, Optional
from functools import wraps
from collections import OrderedDict
from pprint import pformat
from flask import request
from src.api.constants import HOST_PASSWD  # type: ignore
from src.common.helpers import log_exception
from src.common.logger_setup import logger

class InvalidContainerNameError(Exception):
    pass

def log_request(func: Callable) -> Callable:
    """Decorator for logging funcname and *args/**kwargs

    Args:
        func (Callable): Function to be decorated.

    Returns:
        Callable: Decorated function
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        request_json = None
        try:
            if request.is_json:
                request_json = request.get_json()
        except Exception:
            log_exception(
                message="Failed to get json from request object",
                data={
                    "request": request
                }
            )

        logger.info(
            "\n\n"
            + pformat(
                OrderedDict(
                    {
                        "msg": "Logging Func Invocation:",
                        "funcname": func.__name__,
                        "args": args,
                        "kwargs": kwargs,
                        "request_json": request_json,
                    }
                )
            )
        )
        return func(*args, **kwargs)

    return decorated_function


def seconds_to_string(seconds: int) -> str:
    """Converts seconds as an int to a human-readable string of the duration.

    Eg,
    - `788645` seconds becomes
    - "1 week, 2 days, 3 hours, 4 minutes, 5 seconds"

    Args:
        seconds (int): Seconds as an int

    Returns:
        str: Human-readable duration string of the number of seconds.
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    w, d = divmod(d, 7)

    parts = []
    if w:
        parts.append(f"{int(w)} weeks")
    if d:
        parts.append(f"{int(d)} days")
    if h:
        parts.append(f"{int(h)} hours")
    if m:
        parts.append(f"{int(m)} minutes")
    if s:
        parts.append(f"{int(s)} seconds")

    return ", ".join(parts)

def container_name_to_container(client: docker.client, container_name: str) -> Container:
    """Uses docker-py to convert a container name string to a Container object

    Args:
        client (docker.client): Instantiated docker client
        container_name (str): Name of container

    Returns:
        Container: Returns a Container if a matching one is found. None otherwise.

    Raises:
        InvalidContainerNameError: If we cannot find a container by the name `container_name`
    """
    try:
        container = client.containers.get(container_name)
        return container
    except docker.errors.NotFound:
        raise InvalidContainerNameError(f"Tried sending a command to container '{container_name}' but a container by that name did not exist!")

PASSWD_RE = r"\n(?P<user>[^:]+):\w+:{uid}:\d+:.*\n"
def get_running_username() -> str:
    """Get the name of linux user running the API

    Returns:
        str: Username of running user
    """
    uid = os.getuid()
    with open(HOST_PASSWD, "r") as f:
        contents = f.read()
        regex = PASSWD_RE.format(uid=uid)
        resp = re.search(regex, contents)

        if resp == None:
            logger.info(regex)
            logger.info(contents)
            logger.info(resp)
            raise RuntimeError(f"Could not deduce the username for uid '{uid}'!")
        return resp.group(1)