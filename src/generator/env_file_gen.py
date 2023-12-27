#!/bin/env python3

import os
import socket
from src.common.paths import ServerPaths

from pprint import pformat
from typing import Dict
from pathlib import Path

from src.api.constants import IS_PROD_HOST

from src.common.logger_setup import logger
from src.generator.constants import DEFAULT_CHMOD_MODE
from src.generator.base_generator import BaseGenerator

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

        self.generated_env_file_path = ServerPaths.get_generated_env_file_path(env)
        if not self.generated_env_file_path.parent.exists():
            self.generated_env_file_path.parent.mkdir()
        self.env = env

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
        

    @staticmethod
    def dump_write_cb(f, config):
        logger.info(pformat(config))
        for key, value in config.items():
            f.write(f'{key}="{value}"\n'.encode("utf8"))

    def dump_generated_env_file(self):
        logger.info(f"Generating new {self.generated_env_file_path}...")

        self.write_config(
            self.generated_env_file_path,
            self.generated_env_config,
            (
                "#\n"
                "# THIS FILE WAS AUTOMATICALLY GENERATED\n"
                "# DO NOT MODIFY MANUALLY\n"
                "# CHANGES WILL BE OVERWRITTEN ON RESTART\n"
                "#"
                f"# MODIFY `env/{self.env}.toml` FOR PERMANENT CHANGES"
                "#\n\n"
            ),
            EnvFileGen.dump_write_cb
        )

        logger.info("Done.")
