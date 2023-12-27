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
