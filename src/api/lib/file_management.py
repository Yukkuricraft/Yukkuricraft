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

class FileManager:
    ALLOWED_PATHS: List[Path] = [
        Path("env/"),
        Path("secrets/configs"),
    ]
    ALLOWED_FILES: List[Path] = [
    ]

    @classmethod
    def validate_write_path(cls, file: Path) -> bool:
        for path in cls.ALLOWED_PATHS:
            try:
                file.relative_to(path)
                return True
            except ValueError:
                pass

        for path in cls.ALLOWED_FILES:
            if file == path:
                return True

        return False

    @staticmethod
    def ls(path: Path):
        if not FileManager.validate_write_path(path):
            raise ValueError("Illegal write path specified.")

        items = sorted(path.iterdir())
        return {
            "path": str(path),
            "ls": items,
        }

    @staticmethod
    def read(file: Path):
        if not FileManager.validate_write_path(file):
            raise ValueError("Illegal write path specified.")

        content = ""
        try:
            with open(f"/app/{file}", 'r') as f:
                content = f.read()
        except:
            pass
        return {
            "file": str(file),
            "content": content,
        }

    @staticmethod
    def write(file: Path, content: str):
        if not FileManager.validate_write_path(file):
            raise ValueError("Illegal write path specified.")

        try:
            with open(f"/app/{file}", 'w') as f:
                f.write(content)
        except Exception as e:
            logger.warning(pformat(e))

        return {
            "file": str(file),
            "content": content,
        }