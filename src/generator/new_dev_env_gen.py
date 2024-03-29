#!/bin/env python3

from collections import OrderedDict
import os
from src.common.config import load_env_config
from src.common.config.env_config import EnvConfig
from src.common.constants import (
    DEFAULT_CHMOD_MODE,
    BASE_DATA_PATH,
    REPO_ROOT_PATH,
)
from src.generator.constants import (
    SERVER_PROPERTIES_TEMPLATE_PATH,
)
from src.common.server_type_actions import ServerTypeActions
from src.common.helpers import recursive_chmod  # type: ignore
from src.common.paths import ServerPaths
from src.common.logger_setup import logger
from src.common.types import DataDirType
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

        curr_dir = Path(__file__).parent
        self.server_properties_template = load_env_config(
            curr_dir / str(SERVER_PROPERTIES_TEMPLATE_PATH)
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
        self.generate_prereq_dirs(new_env)

        ServerTypeActions().perform_only_once_actions(Env(new_env))

    ENV_CONFIG_SECTION_ORDER = [
        "general",
        "world-groups",
        "cluster-variables",
    ]

    def copy_env_config(self) -> Dict:
        src_config = self.env.config.as_dict()
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

        if "cluster-variables" not in copied_config:
            copied_config["cluster-variables"] = {}
        copied_config["cluster-variables"]["ENV"] = new_env
        copied_config["cluster-variables"]["ENV_ALIAS"] = env_alias
        copied_config["cluster-variables"]["VELOCITY_PORT"] = velocity_port
        copied_config["cluster-variables"]["MC_TYPE"] = server_type

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

    def generate_prereq_dirs(self, new_env: str):
        default_configs_path = ServerPaths.get_env_default_configs_path(new_env)
        paths = [
            default_configs_path / "server",
            default_configs_path / "plugins",
            default_configs_path / "mods",
            ServerPaths.get_env_default_mods_path(new_env),
            ServerPaths.get_env_default_plugins_path(new_env),
            ServerPaths.get_mc_env_data_path(new_env),
            ServerPaths.get_mysql_env_data_path(new_env),
            ServerPaths.get_pg_env_data_path(new_env),
        ]

        for path in paths:
            if not path.exists():
                logger.info(f"Generating {path}...")
                path.mkdir(parents=True)

        # World dirs
        for world in self.env.world_groups:
            logger.info("\n")
            logger.info(f"Generating dirs for {world}")

            paths = [
                ServerPaths.get_env_and_world_group_configs_path(new_env, world),
            ]
            for data_file_type in DataDirType:
                paths.append(
                    ServerPaths.get_data_dir_path(new_env, world, data_file_type)
                )

            for path in paths:
                if not path.exists():
                    logger.info(f"Generating {path}...")
                    path.mkdir(parents=True)

            server_properties_path = ServerPaths.get_server_properties_path(
                new_env, world
            )
            if not server_properties_path.parent.exists():
                server_properties_path.parent.mkdir(parents=True)

            template = self.server_properties_template.as_dict()
            template["level-name"] = world

            if not server_properties_path.exists():
                logger.info(
                    f">> Generating server.properties at {server_properties_path}..."
                )

                self.write_config(
                    server_properties_path,
                    template,
                    "# This file was generated from a template",
                    lambda f, config: EnvConfig.write_cb(f, config, quote=False),
                )

                os.chmod(server_properties_path, DEFAULT_CHMOD_MODE)