#!/bin/env python3

from collections import OrderedDict
import os
from src.common.config import load_env_config
from src.common.config.env_config import EnvConfig
from src.generator.constants import (
    DEFAULT_CHMOD_MODE,
    BASE_DATA_PATH,
    REPO_ROOT_PATH,
    SERVER_PROPERTIES_TEMPLATE_PATH,
)
from src.generator.server_type_actions import ServerTypeActions
from src.common.helpers import recursive_chmod  # type: ignore
from src.common.paths import ServerPaths
from src.common.logger_setup import logger
from src.common.types import DataFileType
import shutil

from typing import Dict
from pathlib import Path

from src.common.environment import Env

from src.generator.base_generator import BaseGenerator

"""
TODO: Configurable copying of certain folders/configs from a source env
"""

class NewDevEnvGen(BaseGenerator):
    server_root: Path

    def __init__(self, base_env: Env):
        super().__init__(base_env)

        self.server_type_actions = ServerTypeActions(base_env)

        curr_dir = Path(__file__).parent
        self.server_properties_template = load_env_config(
            str(SERVER_PROPERTIES_TEMPLATE_PATH), curr_dir
        )

    def run(
        self,
        new_env: str,
        velocity_port: int,
        env_alias: str,
        enable_env_protection: bool,
        server_type: str,
        description: str,
    ):
        logger.info("Generating New Environment Directories")
        logger.info(f"- Repo Root: {REPO_ROOT_PATH}")
        logger.info(f"- Server Root: {BASE_DATA_PATH}")
        logger.info(f"- Base Env: {self.env.name}")
        logger.info(f"- New Env: {new_env}")
        logger.info(f"- Enable Env Protection: {enable_env_protection}")
        logger.info(f"- Server Type:\n{server_type}")
        logger.info(f"- Description:\n{description}")
        logger.info("\n")

        self.generate_env_config(
            new_env,
            velocity_port,
            env_alias,
            enable_env_protection,
            server_type,
            description,
        )
        self.generate_config_dirs(new_env)

        self.server_type_actions.run(Env(new_env), server_type)

    ENV_CONFIG_SECTION_ORDER = [
        "general",
        "world-groups",
        "runtime-environment-variables",
    ]

    def copy_env_config(self) -> Dict:
        src_config = self.env.config
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
        self,
        new_env: str,
        velocity_port: int,
        env_alias: str,
        enable_env_protection: bool,
        server_type: str,
        description: str,
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

        new_config_path = ServerPaths.get_env_toml_config_path(new_env)

        self.write_config(
            new_config_path,
            copied_config,
            (
                "#\n"
                f"# THIS FILE WAS AUTOMAGICALLY GENERATED USING env/{self.env.name}.toml AS A BASE\n"
                "# MODIFY AS NECESSARY BY HAND\n"
                "# SEE env1.toml FOR HELPFUL COMMENTS RE: CONFIG PARAMS\n"
                "#\n\n"
            ),
        )

    def generate_config_dirs(self, new_env: str):
        # World dirs
        for world in self.env.world_groups:
            logger.info("\n")
            logger.info(f"Generating dirs for {world}")

            world_config_path = ServerPaths.get_env_and_world_group_configs_path(
                new_env, world
            )
            if not world_config_path.exists():
                logger.info(f">> Generating {world_config_path}...")
                world_config_path.mkdir(parents=True)

            mods_path = ServerPaths.get_data_files_path(new_env, world, DataFileType.MOD_CONFIGS)
            if not mods_path.exists():
                logger.info(f">> Generating {mods_path}...")
                mods_path.mkdir(parents=True)

            server_only_mods_path = ServerPaths.get_data_files_path(new_env, world, DataFileType.SERVER_ONLY_MOD_FILES)
            if not server_only_mods_path.exists():
                logger.info(f">> Generating {server_only_mods_path}...")
                server_only_mods_path.mkdir(parents=True)

            plugins_path = ServerPaths.get_data_files_path(
                new_env, world, DataFileType.PLUGIN_CONFIGS
            )
            if not plugins_path.exists():
                logger.info(f">> Generating {plugins_path}...")
                plugins_path.mkdir(parents=True)

            worlds_path = ServerPaths.get_data_files_path(new_env, world, DataFileType.SERVER_CONFIGS)
            if not worlds_path.exists():
                logger.info(f">> Generating {worlds_path}...")
                worlds_path.mkdir(parents=True)

            self.server_properties_path = ServerPaths.get_server_properties_path(
                new_env, world
            )
            if not self.server_properties_path.parent.exists():
                self.server_properties_path.parent.mkdir(parents=True)

            template = self.server_properties_template.as_dict()
            template["level-name"] = world

            if not self.server_properties_path.exists():
                logger.info(
                    f">> Generating server.properties at {self.server_properties_path}..."
                )

                self.write_config(
                    self.server_properties_path,
                    template,
                    "# This file was generated from a template",
                    lambda f, config: EnvConfig.write_cb(f, config, quote=False),
                )

                os.chmod(self.server_properties_path, DEFAULT_CHMOD_MODE)

        # Should this get copied? Maybe delegate to ServerTypeActions?

        # Copy default secret world configs from {self.env} to {new_env}
        src_default_path = ServerPaths.get_env_default_configs_path(self.env.name)
        dst_default_path = ServerPaths.get_env_default_configs_path(new_env)
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
