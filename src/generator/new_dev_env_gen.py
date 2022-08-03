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

from src.generator.constants import SECRETS_CONFIG_RELPATH

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
TODO: Configurable copying of certain folders/configs from a source env
"""


class NewDevEnvGen(BaseGenerator):
    repo_root: Path

    def __init__(self, base_env: str):
        super().__init__(base_env)

        self.repo_root = Path(
            self.env_config["runtime-environment-variables"].YC_REPO_ROOT
        )

    def run(self, new_env: str, velocity_port: int):
        logger.info("Generating New Environment Directories")
        logger.info(f"- Repo Root: {self.repo_root}")
        logger.info(f"- Base Env: {self.env}")
        logger.info(f"- New Env: {new_env}")
        logger.info("\n")

        self.generate_env_config(new_env, velocity_port)
        self.generate_secrets_config_dirs(new_env)

    def generate_env_config(self, new_env: str, velocity_port: int):
        """
        We copy and make necessary adjustments to the {self.env} config to create a new {self.new_env} config.
        """

        src_config = self.env_config.as_dict()
        src_config["runtime-environment-variables"]["ENV"] = new_env
        src_config["runtime-environment-variables"]["VELOCITY_PORT"] = velocity_port

        new_config_path = self.repo_root / "env" / f"{new_env}.toml"
        with open(new_config_path, "wb") as f:
            f.write(
                (
                    "#\n"
                    f"# THIS FILE WAS AUTOMAGICALLY GENERATED USING env/{self.env}.toml AS A BASE\n"
                    "# MODIFY AS NECESSARY BY HAND\n"
                    "# SEE prod.toml FOR HELPFUL COMMENTS RE: CONFIG PARAMS\n"
                    "#\n\n"
                ).encode("utf8")
            )
            tomli_w.dump(src_config, f)

    PLUGINS_CONFIG_DIR = "plugins"
    WORLDS_CONFIG_DIR = "server"
    SECRETS_CONFIG_RELPATH: str = "secrets/configs/"

    def generate_secrets_config_dirs(self, new_env: str):

        # Nginx dir (Empty for now?)
        nginx_config_path = (
            self.repo_root / self.SECRETS_CONFIG_RELPATH / new_env / "nginx"
        )
        if not nginx_config_path.exists():
            logger.info(f"Generating {nginx_config_path}...")
            nginx_config_path.mkdir(parents=True)

        # World dirs
        for world in self.env_config["world-groups"].enabled_groups:
            logger.info("\n")
            logger.info(f"Generating dirs for {world}")

            secrets_world_config_path = (
                self.repo_root
                / self.SECRETS_CONFIG_RELPATH
                / new_env
                / "worlds"
                / world
            )
            if not secrets_world_config_path.exists():
                logger.info(f">> Generating {secrets_world_config_path}...")
                secrets_world_config_path.mkdir(parents=True)

            plugins_path = secrets_world_config_path / self.PLUGINS_CONFIG_DIR
            if not plugins_path.exists():
                logger.info(f">> Generating {plugins_path}...")
                plugins_path.mkdir(parents=True)

            worlds_path = secrets_world_config_path / self.WORLDS_CONFIG_DIR
            if not worlds_path.exists():
                logger.info(f">> Generating {worlds_path}...")
                worlds_path.mkdir(parents=True)

            src_server_properties_path = (
                self.repo_root
                / self.SECRETS_CONFIG_RELPATH
                / self.env
                / "worlds"
                / world
                / self.WORLDS_CONFIG_DIR
                / "server.properties"
            )
            dst_server_properties_path = worlds_path / "server.properties"

            if not dst_server_properties_path.exists():
                logger.info(
                    f">> Copying world server.properties from {src_server_properties_path} to {dst_server_properties_path}..."
                )
                parent_path = dst_server_properties_path.parent
                if not parent_path.exists():
                    parent_path.mkdir(parents=True)
                shutil.copy(src_server_properties_path, dst_server_properties_path)

        # Copy default secret world configs from {self.env} to {new_env}
        src_default_path = (
            self.repo_root
            / self.SECRETS_CONFIG_RELPATH
            / self.env
            / "worlds"
            / "default"
        )
        dst_default_path = (
            self.repo_root
            / self.SECRETS_CONFIG_RELPATH
            / new_env
            / "worlds"
            / "default"
        )
        if not dst_default_path.exists():
            logger.info(
                f"Copying default config files from {src_default_path} to {dst_default_path}..."
            )
            shutil.copytree(src_default_path, dst_default_path)
        else:
            logger.info(
                f"Skipped copying files from {src_default_path} to {dst_default_path} as destination directory already existed."
            )
            logger.info(
                "This script did not validate that the contents of {dst_default_path} was valid - please confirm this manually."
            )
