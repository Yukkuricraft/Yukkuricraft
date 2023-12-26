#!/bin/env python3

from collections import OrderedDict
import copy
import os
import stat
import yaml # type: ignore
from src.generator.constants import DEFAULT_CHMOD_MODE
from src.common.helpers import recursive_chmod  # type: ignore
import tomli_w # type: ignore
import shutil

yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
)

from typing import Dict
from pathlib import Path

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

        self.repo_root = Path(__file__).parent.parent.parent  # G w o s s
        self.server_root = Path("/var/lib/yukkuricraft")

    def run(self, new_env: str, velocity_port: int, env_alias: str, enable_env_protection: bool, server_type: str, description: str):
        logger.info("Generating New Environment Directories")
        logger.info(f"- Repo Root: {self.repo_root}")
        logger.info(f"- Server Root: {self.server_root}")
        logger.info(f"- Base Env: {self.env}")
        logger.info(f"- New Env: {new_env}")
        logger.info(f"- Enable Env Protection: {enable_env_protection}")
        logger.info(f"- Server Type:\n{server_type}")
        logger.info(f"- Description:\n{description}")
        logger.info("\n")

        self.generate_env_config(new_env, velocity_port, env_alias, enable_env_protection, server_type, description)
        self.generate_config_dirs(new_env)
        self.generate_server_type_specific_configs(server_type)

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
        self, new_env: str, velocity_port: int, env_alias: str, enable_env_protection: bool, server_type: str, description: str
    ):
        """
        We copy and make necessary adjustments to the {self.env} config to create a new {self.new_env} config.
        """

        copied_config = self.copy_env_config()

        if "general" not in copied_config:
            copied_config["general"] = {}
        copied_config["general"]["description"] = description
        copied_config["general"]["enable_env_protection"] = enable_env_protection
        copied_config["general"]["enable_backups"] = False

        if "runtime-environment-variables" not in copied_config:
            copied_config["runtime-environment-variables"] = {}
        copied_config["runtime-environment-variables"]["ENV"] = new_env
        copied_config["runtime-environment-variables"]["ENV_ALIAS"] = env_alias
        copied_config["runtime-environment-variables"]["VELOCITY_PORT"] = velocity_port
        copied_config["runtime-environment-variables"]["MC_TYPE"] = server_type

        new_config_path = self.repo_root / "env" / f"{new_env}.toml"

        self.write_config(
            new_config_path,
            copied_config,
            (
                "#\n"
                f"# THIS FILE WAS AUTOMAGICALLY GENERATED USING env/{self.env}.toml AS A BASE\n"
                "# MODIFY AS NECESSARY BY HAND\n"
                "# SEE env1.toml FOR HELPFUL COMMENTS RE: CONFIG PARAMS\n"
                "#\n\n"
            )
        )

    MODS_CONFIG_DIR = "mods"
    PLUGINS_CONFIG_DIR = "plugins"
    WORLDS_CONFIG_DIR = "server"

    def generate_config_dirs(self, new_env: str):
        # World dirs
        for world in self.get_enabled_world_groups():
            logger.info("\n")
            logger.info(f"Generating dirs for {world}")

            world_config_path = (
                self.server_root
                / "env"
                / new_env
                / world
                / "configs"
            )
            if not world_config_path.exists():
                logger.info(f">> Generating {world_config_path}...")
                world_config_path.mkdir(parents=True)

            mods_path = world_config_path / self.MODS_CONFIG_DIR
            if not mods_path.exists():
                logger.info(f">> Generating {mods_path}...")
                mods_path.mkdir(parents=True)

            plugins_path = world_config_path / self.PLUGINS_CONFIG_DIR
            if not plugins_path.exists():
                logger.info(f">> Generating {plugins_path}...")
                plugins_path.mkdir(parents=True)

            worlds_path = world_config_path / self.WORLDS_CONFIG_DIR
            if not worlds_path.exists():
                logger.info(f">> Generating {worlds_path}...")
                worlds_path.mkdir(parents=True)

            src_server_properties_path = (
                self.server_root
                / "env"
                / self.env
                / world
                / "configs"
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
                os.chmod(dst_server_properties_path, DEFAULT_CHMOD_MODE)

        # Copy default secret world configs from {self.env} to {new_env}
        src_default_path = (
            self.server_root
            / "env"
            / self.env
            / "defaultconfigs"
        )
        dst_default_path = (
            self.server_root
            / "env"
            / new_env
            / "defaultconfigs"
        )
        if not dst_default_path.exists():
            logger.info(
                f"Copying default config files from {src_default_path} to {dst_default_path}..."
            )
            shutil.copytree(src_default_path, dst_default_path)
            recursive_chmod(dst_default_path, DEFAULT_CHMOD_MODE)
        else:
            logger.info(
                f"Skipped copying files from {src_default_path} to {dst_default_path} as destination directory already existed."
            )
            logger.info(
                f"This script did not validate that the contents of {dst_default_path} was valid - please confirm this manually."
            )

    def generate_server_type_specific_configs(self, server_type: str):
        logger.info("Doing server type specific stuff?")

        if server_type in ["FABRIC", "FORGE"]:
            pass
        elif server_type in ["PAPER", "BUKKIT"]:
            pass
        else:
            logger.info(f"No special actions taken for serer type: {server_type}")