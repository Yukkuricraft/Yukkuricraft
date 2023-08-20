#!/bin/env python3

import os
import copy
import yaml  # type: ignore

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
    prod_nginx_http_port = "80"
    prod_nginx_https_port = "443"
    dev_api_host = "dev.api.yukkuricraft.net"
    dev_nginx_http_port = "8080"
    dev_nginx_https_port = "444"
    def generate_env_file(self):
        self.generated_env_config = self.env_config[
            "runtime-environment-variables"
        ].as_dict()

        self.generated_env_config["ENV"] = self.env
        self.generated_env_config["API_HOST"] = self.prod_api_host if IS_PROD_HOST else self.dev_api_host
        self.generated_env_config["NGINX_PROXY_HTTP_PORT"] = self.prod_nginx_http_port if IS_PROD_HOST else self.dev_nginx_http_port
        self.generated_env_config["NGINX_PROXY_HTTPS_PORT"] = self.prod_nginx_https_port if IS_PROD_HOST else self.dev_nginx_https_port

    def dump_generated_env_file(self):
        print(f"Generating new {self.generated_env_file_path}...")

        generated_env_file_path = self.get_generated_env_file_path()
        generated_env_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(generated_env_file_path, "w") as f:
            f.write(
                "#\n"
                "# THIS FILE WAS AUTOMATICALLY GENERATED\n"
                "# DO NOT MODIFY MANUALLY\n"
                "# CHANGES WILL BE OVERWRITTEN ON RESTART\n"
                "#"
                f"# MODIFY `env/{self.env}.toml` FOR PERMANENT CHANGES"
                "#\n\n"
            )
            for key, value in self.generated_env_config.items():
                f.write(f'{key}="{value}"\n')
        os.chmod(generated_env_file_path, DEFAULT_CHMOD_MODE)
        print("Done.")
