#!/bin/env python3

from collections import OrderedDict
import os
from src.common.config import load_env_config
from src.common.config.env_config import EnvConfig
from src.common.constants import (
    DEFAULT_CHMOD_MODE,
    BASE_DATA_PATH,
    REPO_ROOT_PATH,
    HOST_REPO_ROOT_PATH
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

from src.api.constants import (
    HOSTNAME
)

from src.generator.base_generator import BaseGenerator

class WorldGroupFilesGen(BaseGenerator):
    server_root: Path

    def __init__(self, env: Env):
        super().__init__(env)

        curr_dir = Path(__file__).parent
        self.server_properties_template = load_env_config(
            curr_dir / str(SERVER_PROPERTIES_TEMPLATE_PATH)
        )

    def run(self):
        logger.info("Generating World Group Directories")
        logger.info(f"- Repo Root: {REPO_ROOT_PATH}")
        logger.info(f"- Server Root: {BASE_DATA_PATH}")
        logger.info(f"- Base Env: {self.env.name}")
        logger.info("\n")

        self.generate_files_and_dirs()

    ENV_CONFIG_SECTION_ORDER = [
        "general",
        "world-groups",
        "cluster-variables",
    ]

    def generate_files_and_dirs(self):
        env = self.env.name

        for world in self.env.world_groups:
            logger.info("\n")
            logger.info(f"Generating dirs for {world}")

            paths = [
                ServerPaths.get_env_and_world_group_configs_path(env, world),
            ]
            for data_file_type in DataDirType:
                paths.append(
                    ServerPaths.get_data_dir_path(env, world, data_file_type)
                )

            for path in paths:
                if not path.exists():
                    logger.info(f"Generating {path}...")
                    path.mkdir(parents=True)

            server_properties_path = ServerPaths.get_server_properties_path(
                env, world
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