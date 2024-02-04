#!/usr/bin/env python3

import os
from typing import Dict, Callable, Optional
from pathlib import Path

from src.common.environment import Env
from src.common.helpers import write_config
from src.common.config.toml_config import TomlConfig

class BaseGenerator:
    WORLDGROUP_NAME_BLOCKLIST = [
        "defaultconfigs",  # :`) Ugly folder structures yay`
    ]

    def __init__(self, env: Env):
        self.env = env

    def replace_interpolations(self, inp, replace_value: str):
        """
        Please for the love of god refactor me in the future.
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
            return inp.replace("<<WORLDGROUP>>", replace_value)
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