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
        ServerTypeActions().perform_only_once_actions(Env(new_env))

    ENV_CONFIG_SECTION_ORDER = [
        "general",
        "world-groups",
        "cluster-variables",
    ]

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

        config = {}

        config["general"] = {}
        config["general"]["description"] = description
        config["general"]["enable_env_protection"] = enable_env_protection
        config["general"]["enable_backups"] = False
        config["general"]["hostname"] = HOSTNAME

        config["world-groups"] = {}
        config["world-groups"]["enabled_groups"] = [
            "lobby"
        ]

        config["cluster-variables"] = {}
        config["cluster-variables"]["ENV_ALIAS"] = env_alias
        config["cluster-variables"]["VELOCITY_PORT"] = velocity_port
        config["cluster-variables"]["MC_TYPE"] = server_type
        config["cluster-variables"]["MC_FS_ROOT"] = str(BASE_DATA_PATH)
        config["cluster-variables"]["MC_VERSION"] = "1.21.1"
        config["cluster-variables"]["YC_REPO_ROOT"] = str(HOST_REPO_ROOT_PATH)
        config["cluster-variables"]["BACKUPS_ROOT"] = str(BASE_DATA_PATH / "backups")

        new_config_path = ServerPaths.get_env_toml_config_path(new_env)

        self.write_config(
            new_config_path,
            config,
            (
                "#\n"
                f"# THIS FILE WAS AUTOMAGICALLY GENERATED USING env/{self.env.name}.toml AS A BASE\n"
                "# MODIFY AS NECESSARY BY HAND\n"
                "# SEE env1.toml FOR HELPFUL COMMENTS RE: CONFIG PARAMS\n"
                "#\n\n"
            ),
        )