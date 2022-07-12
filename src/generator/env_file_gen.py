#!/bin/env python3

import copy
import yaml  # type: ignore
import tomli_w
import shutil

yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
)

from typing import Dict
from pathlib import Path

from src.generator.base_generator import BaseGenerator
from src.common.yaml_config import YamlConfig
from src.common.toml_config import TomlConfig
from src.common.config import load_yaml_config, load_toml_config

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

logger.addHandler(ch)

"""
Generate .env files for use with docker-compose.

Since .env files only accept key-value pairs, our implementation makes a Dict[str, str] assumption for the generated config.
As such an ENV.toml that defines non-string values for keys in '[runtime-environment-variables]' may cause issues.
"""
class EnvFileGen(BaseGenerator):
    repo_root: Path
    generated_env_file_name: str
    generated_env_file_path: Path

    generated_env_config: Dict[str, str]

    def __init__(self, env: str):
        super().__init__(env)

        self.repo_root = Path(self.env_config["runtime-environment-variables"].YC_REPO_ROOT)
        self.generated_env_file_name = f"{env}.env"
        self.generated_env_file_path = self.repo_root / "gen"

    def run(self):
        self.generate_env_file()
        self.dump_generated_env_file()

    def generate_env_file(self):
        self.generated_env_config = self.env_config['runtime-environment-variables'].as_dict()

    def dump_generated_env_file(self):
        print(f"Generating new {self.generated_env_file_path}...")

        generated_env_file_path = self.generated_env_file_path / self.generated_env_file_name
        with open(generated_env_file_path, "w") as f:
            f.write(
                "#\n"
                "# THIS FILE WAS AUTOMATICALLY GENERATED\n"
                "# DO NOT MODIFY MANUALLY\n"
                "# CHANGES WILL BE OVERWRITTEN ON RESTART\n"
                "#\n\n"
            )
            for key, value in self.generated_env_config.items():
                f.write(f"{key}=\"{value}\"\n")
        print("Done. Not. Implement me.")

