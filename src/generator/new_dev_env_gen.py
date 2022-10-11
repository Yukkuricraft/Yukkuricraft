#!/bin/env python3

from collections import OrderedDict
import copy
import yaml  # type: ignore
import tomli_w # type: ignore
import shutil

yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
)

from typing import Dict
from pathlib import Path

from src.generator.constants import SECRETS_CONFIG_RELPATH

from src.generator.base_generator import BaseGenerator

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
    server_root: Path

    def __init__(self, base_env: str):
        super().__init__(base_env)

        self.server_root = Path(__file__).parent.parent.parent  # G w o s s

    def run(self, new_env: str, velocity_port: int, env_alias: str, description: str):
        logger.info("Generating New Environment Directories")
        logger.info(f"- Repo Root: {self.server_root}")
        logger.info(f"- Base Env: {self.env}")
        logger.info(f"- New Env: {new_env}")
        logger.info(f"- Description:\n{description}")
        logger.info("\n")

        self.generate_env_config(new_env, velocity_port, env_alias, description)
        self.generate_secrets_config_dirs(new_env)

    ENV_CONFIG_SECTION_ORDER = [
        "general",
        "world-groups",
        "runtime-environment-variables",
    ]

    def copy_env_config(self) -> Dict:
        src_config = self.env_config.as_dict()
        copied_config = OrderedDict()

        # Copy configured/sorted sections first
        for key in self.ENV_CONFIG_SECTION_ORDER:
            if key in src_config:
                copied_config[key] = src_config[key]
            else:
                copied_config[key] = {}

        # Copy the rest at the end of the config
        for key, values in src_config.items():
            if key not in copied_config:
                copied_config[key] = values

        return copied_config

    def generate_env_config(
        self, new_env: str, velocity_port: int, env_alias: str, description: str
    ):
        """
        We copy and make necessary adjustments to the {self.env} config to create a new {self.new_env} config.
        """

        copied_config = self.copy_env_config()

        if "general" not in copied_config:
            copied_config["general"] = {}
        copied_config["general"]["description"] = description

        if "runtime-environment-variables" not in copied_config:
            copied_config["runtime-environment-variables"] = {}
        copied_config["runtime-environment-variables"]["ENV"] = new_env
        copied_config["runtime-environment-variables"]["ENV_ALIAS"] = env_alias
        copied_config["runtime-environment-variables"]["VELOCITY_PORT"] = velocity_port

        new_config_path = self.server_root / "env" / f"{new_env}.toml"
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
            tomli_w.dump(copied_config, f, multiline_strings=True)

    PLUGINS_CONFIG_DIR = "plugins"
    WORLDS_CONFIG_DIR = "server"
    SECRETS_CONFIG_RELPATH: str = "secrets/configs/"

    def generate_secrets_config_dirs(self, new_env: str):

        # Nginx dir (Empty for now?)
        nginx_config_path = (
            self.server_root / self.SECRETS_CONFIG_RELPATH / new_env / "nginx"
        )
        if not nginx_config_path.exists():
            logger.info(f"Generating {nginx_config_path}...")
            nginx_config_path.mkdir(parents=True)

        # World dirs
        for world in self.env_config["world-groups"].enabled_groups:
            logger.info("\n")
            logger.info(f"Generating dirs for {world}")

            secrets_world_config_path = (
                self.server_root
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
                self.server_root
                / self.SECRETS_CONFIG_RELPATH
                / self.env
                / "worlds"
                / world
                / self.WORLDS_CONFIG_DIR
                / "server.properties"
            )
            dst_server_properties_path = worlds_path / "server.properties"

            if not dst_server_properties_path.exists():
                if not src_server_properties_path.exists():
                    pass
                logger.info(
                    f">> Copying world server.properties from {src_server_properties_path} to {dst_server_properties_path}..."
                )
                parent_path = dst_server_properties_path.parent
                if not parent_path.exists():
                    parent_path.mkdir(parents=True)
                shutil.copy(src_server_properties_path, dst_server_properties_path)

        # Copy default secret world configs from {self.env} to {new_env}
        src_default_path = (
            self.server_root
            / self.SECRETS_CONFIG_RELPATH
            / self.env
            / "worlds"
            / "default"
        )
        dst_default_path = (
            self.server_root
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
