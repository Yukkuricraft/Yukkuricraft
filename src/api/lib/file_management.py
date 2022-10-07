import json
import re

from pprint import pformat
from functools import total_ordering
from pathlib import Path
from typing import Callable, List, Optional

from src.api.constants import ENV_FOLDER, MIN_VALID_PROXY_PORT, MAX_VALID_PROXY_PORT
from src.api.lib.runner import Runner
from src.common.config import load_toml_config
from src.common.logger_setup import logger
from src.generator.generator import GeneratorType, get_generator

# TODO: Do we validate path by it existing? Whitelisting? Etc

class FileManager:
    @staticmethod
    def ls(path: Path):
        return {
            "tee": "hee",
            "path": str(path),
        }

    @staticmethod
    def read(file: Path):
        content = ""
        try:
            with open(f"/app/{file}", 'r') as f:
                content = f.read()
        except:
            pass
        return {
            "tee": "hee",
            "file": str(file),
            "content": content,
        }
    
    @staticmethod
    def write(file: Path, content: str):
        return {
            "tee": "hee",
            "file": str(file),
            "content": content,
        }