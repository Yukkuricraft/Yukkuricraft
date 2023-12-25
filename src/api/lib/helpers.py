from typing import Callable
from functools import wraps
from collections import OrderedDict
from pprint import pformat
from src.common.logger_setup import logger

def log_request(func: Callable):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        logger.info("\n\n" + pformat(OrderedDict({
          "msg":"Logging Request Payload:",
          "funcname": func.__name__,
          "args": args,
          "kwargs": kwargs
        })))
        return func(*args, **kwargs)

    return decorated_function
