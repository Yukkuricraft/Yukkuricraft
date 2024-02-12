#!/usr/bin/env python3

import os
from typing import Any, Dict, Callable, Optional, TypeVar
from pathlib import Path

from src.common.environment import Env
from src.common.helpers import write_config
from src.common.config.toml_config import TomlConfig

T = TypeVar("T")
class BaseGenerator:
    WORLDGROUP_NAME_BLOCKLIST = [
        "defaultconfigs",  # :`) Ugly folder structures yay`
    ]

    def __init__(self, env: Env):
        self.env = env

    def replace_interpolations(self, inp: T, target: str, replace_value: str) -> T:
        """Given some primitive datastructure `inp`, will replace any instance of `target` in both keys and vals with `replace_value`

        Args:
            inp (T): Any python native datastructure.
            target (str): Target string to replace. Usually of format `<<TARGET>>`.
            replace_value (str): Value to replace `target` with.

        Returns:
            T: The `inp` with targets replaced.
        """
        if type(inp) == list:
            return [self.replace_interpolations(item, replace_value) for item in inp]
        elif type(inp) == dict:
            return {
                self.replace_interpolations(
                    key, replace_value
                ): self.replace_interpolations(value, replace_value)
                for key, value in inp.items()
            }
        elif type(inp) == str:
            return inp.replace(target, replace_value)
        else:
            return inp

    def write_config(
        self,
        config_path: Path,
        config: Dict,
        header: str = "",
        write_cb: Optional[Callable] = lambda f, config: TomlConfig.write_cb(f, config),
    ):
        """Writes config to path with optional header and custom write cb

        Also applies `constants.DEFAULT_CHMOD_MODE`

        Args:
            config_path (Path): Path
            config (Dict): Config represented as a dict
            header (str, optional): Optional header. Defaults to "".
            write_cb (Optional[Callable], optional): Defaults to a `toml_w.dump()`.
        """
        write_config(config_path, config, header, write_cb)