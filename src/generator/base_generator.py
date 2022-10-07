#!/usr/bin/env python3

from typing import Dict
from pathlib import Path

from src.generator.constants import WORLD_GROUP_CONFIG_NAME
from src.common.config.toml_config import TomlConfig
from src.common.config import load_toml_config


class BaseGenerator:
    env_config: TomlConfig

    def __init__(self, env: str):
        self.env = env

        curr_dir = Path(__file__).parent
        self.env_config = load_toml_config(f"env/{env}.toml", curr_dir)

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
