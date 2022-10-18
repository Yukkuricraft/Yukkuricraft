import json
import re
import stat

from os import stat_result

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
    """
    A lot of this class should really be offloaded to a better technology like Protobufs
    so we aren't hand-adjusting front/backend data formats.
    """
    ALLOWED_PATHS: List[Path] = [
        Path("env/"),
        Path("secrets/configs"),
    ]
    ALLOWED_FILES: List[Path] = [
    ]

    @classmethod
    def validate_path(cls, file: Path) -> bool:
        """
        Hm, do we want to separate valid write vs valid read paths?
        """

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

    FT_BIT_TO_CHAR = {
        '-': stat.S_ISREG,
        'b': stat.S_ISBLK,
        'c': stat.S_ISCHR,
        'C': lambda x: False, # Not supported
        'd': stat.S_ISDIR,
        'D': lambda x: False,
        'l': stat.S_ISLNK,
        'M': lambda x: False,
        'n': lambda x: False,
        'p': stat.S_ISFIFO,
        'P': stat.S_ISPORT, # This vs S_IFPORT - ???
        's': stat.S_ISSOCK,
        '?': lambda x: True, # Always keep this last
    }

    @staticmethod
    def stat_to_file_type(mode: int):
        ft_bit = stat.S_IFMT(mode)

        for char, func in FileManager.FT_BIT_TO_CHAR.items():
            if func(ft_bit):
                return char

        # Do we want to return '?' by default or error out?
        return '?'

    @staticmethod
    def stat_to_mode_bits(bit_str: str):
        return {
            'read': bit_str[0] == 'r',
            'write': bit_str[1] == 'w',
            'execute': bit_str[2] # This line assumes filemode(mode) handles all the non-x chars - ie sStTx-
        }

    @staticmethod
    def convert_stat_to_file_mode_obj(mode: int):
        mode_str = stat.filemode(mode)

        return {
            'file_type': FileManager.stat_to_file_type(mode),
            'global': FileManager.stat_to_mode_bits(mode_str[1:4]),
            'group': FileManager.stat_to_mode_bits(mode_str[4:7]),
            'user': FileManager.stat_to_mode_bits(mode_str[7:10]),
        }

    @staticmethod
    def ls(path: Path):
        if not FileManager.validate_path(path):
            raise ValueError("Illegal path specified.")

        items = sorted(path.iterdir())

        rtn = []
        for item in items:
            # Follow symlink? Do we want to account for symlinks?
            stat_obj = item.stat()
            rtn.append({
                'basename': item.name,
                'dirname': str(item.parent),
                'uid': stat_obj.st_uid,
                'gid': stat_obj.st_gid,
                'file_mode': FileManager.convert_stat_to_file_mode_obj(stat_obj.st_mode),
                'children': [],
                'size_bytes': stat_obj.st_size,
                'modified': stat_obj.st_mtime,
                'created': stat_obj.st_ctime,
            })

        return {
            "path": str(path),
            "ls": rtn,
        }

    @staticmethod
    def read(file: Path):
        if not FileManager.validate_path(file):
            raise ValueError("Illegal path specified.")

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
        if not FileManager.validate_path(file):
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