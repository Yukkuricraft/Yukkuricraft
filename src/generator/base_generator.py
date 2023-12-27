#!/usr/bin/env python3

import os
from typing import Dict, Callable, Optional
from pathlib import Path

from src.generator.constants import DEFAULT_CHMOD_MODE
from src.common.config.toml_config import TomlConfig
from src.common.config import load_toml_config
from src.common.paths import ServerPaths


class BaseGenerator:
    env_config: TomlConfig

    WORLDGROUP_NAME_BLOCKLIST = [
        "defaultconfigs",  # :`) Ugly folder structures yay`
    ]

    def __init__(self, env: str):
        self.env = env

        curr_dir = Path(__file__).parent
        self.env_config = load_toml_config(
            ServerPaths.get_env_toml_config_path(env), curr_dir
        )

    def is_prod(self):
        return self.env == "env1"

    def get_enabled_world_groups(self):
        all_world_groups = self.env_config["world-groups"].get_or_default(
            "enabled_groups", []
        )
        filtered_world_groups = list(
            filter(lambda w: w not in self.WORLDGROUP_NAME_BLOCKLIST, all_world_groups)
        )
        return filtered_world_groups

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

        if not config_path.parent.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "wb") as f:
            f.write(header.encode("utf8"))
            write_cb(f, config)
        os.chmod(config_path, DEFAULT_CHMOD_MODE)
