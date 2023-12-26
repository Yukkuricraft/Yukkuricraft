#!/bin/env python3

import os
import copy
import yaml  # type: ignore
import socket

import tomli_w  # type: ignore
import shutil

yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
)

from typing import Dict
from pathlib import Path

from src.api.constants import IS_PROD_HOST

from src.generator.constants import DEFAULT_CHMOD_MODE
from src.generator.base_generator import BaseGenerator

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
    generated_env_file_name: str
    generated_env_file_path: Path

    generated_env_config: Dict[str, str]

    env: str

    def __init__(self, env: str):
        super().__init__(env)

        self.generated_env_file_name = f"{env}.env"
        self.generated_env_file_path = (
            Path(__file__).parent.parent.parent / "gen"
        )  # G w o s s
        self.env = env

    def get_generated_env_file_path(self):
        return self.generated_env_file_path / self.generated_env_file_name

    def run(self):
        self.generate_env_file()
        self.dump_generated_env_file()

    prod_api_host = "api.yukkuricraft.net"
    dev_api_host = "dev.api.yukkuricraft.net"
    def generate_env_file(self):
        self.generated_env_config = self.env_config[
            "runtime-environment-variables"
        ].as_dict()

        self.generated_env_config["ENV"] = self.env
        self.generated_env_config["API_HOST"] = self.prod_api_host if IS_PROD_HOST else self.dev_api_host
        self.generated_env_config["UID"] = os.getuid()
        self.generated_env_config["GID"] = os.getgid()

        # yc-api relies on hostname to determine prod vs non-prod envs. Docker containers
        # will always return the container id for hostname so we configure the hostname in the compose file.
        self.generated_env_config["HOST_HOSTNAME"] = socket.gethostname()
        

    def dump_write_cb(self, f, config):
        for key, value in config.items():
            f.write(f'{key}="{value}"\n')

    def dump_generated_env_file(self):
        print(f"Generating new {self.generated_env_file_path}...")

        generated_env_file_path = self.get_generated_env_file_path()
        generated_env_file_path.parent.mkdir(parents=True, exist_ok=True)

        self.write_config(
            generated_env_file_path,
            self.generate,
            (
                "#\n"
                "# THIS FILE WAS AUTOMATICALLY GENERATED\n"
                "# DO NOT MODIFY MANUALLY\n"
                "# CHANGES WILL BE OVERWRITTEN ON RESTART\n"
                "#"
                f"# MODIFY `env/{self.env}.toml` FOR PERMANENT CHANGES"
                "#\n\n"
            ),
            self.dump_write_cb
        )

        print("Done.")
