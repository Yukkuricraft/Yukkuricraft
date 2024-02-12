from typing import Callable
from functools import wraps
from collections import OrderedDict
from pprint import pformat
from flask import request  # type: ignore
from src.common.logger_setup import logger


def log_request(func: Callable):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        request_json = None
        try:
            request_json = request.get_json()
        except Exception as e:
            logger.info(e)

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