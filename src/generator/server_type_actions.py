#!/bin/env python3
import yaml  # type: ignore

from pathlib import Path

from src.common.config import ConfigNode, load_yaml_config
from src.common.config.config_finder import ConfigFinder
from src.common.config.yaml_config import YamlConfig
from src.common.types import ServerTypes
from src.common.paths import ServerPaths
from src.common.logger_setup import logger
from src.generator.constants import (
    PAPER_GLOBAL_TEMPLATE_PATH,
    VELOCITY_FORWARDING_SECRET_PATH,
)
from src.generator.base_generator import BaseGenerator


class ServerTypeActions(BaseGenerator):
    server_root: Path

    def __init__(self, base_env: str):
        super().__init__(base_env)

    def run(self, target_env: str, server_type: ServerTypes):
        logger.info("Doing server type specific stuff?")

        if server_type in ["FABRIC", "FORGE"]:
            self.merge_fabric_forge_prereq_mods()
        elif server_type in ["PAPER", "BUKKIT"]:
            self.write_paper_bukkit_configs(target_env)
        else:
            logger.info(f"No special actions taken for serer type: {server_type}")

    def write_paper_bukkit_configs(self, target_env: str):
        paper_global_yml_path = ServerPaths.get_paper_global_yml_path(target_env)
        velocity_forwarding_secret = "CouldNotFindValidSecret?"
        curr_dir = Path(__file__).parent
        velocity_secret_path = ConfigFinder(
            str(VELOCITY_FORWARDING_SECRET_PATH), curr_dir
        ).config_path

        try:
            with open(velocity_secret_path, "r") as f:
                secret = f.read().strip()
                velocity_forwarding_secret = (
                    secret if len(secret) > 0 else velocity_forwarding_secret
                )
        except FileNotFoundError:
            logger.info(f"Could not load {velocity_secret_path}")

        paper_global_tpl = load_yaml_config(str(PAPER_GLOBAL_TEMPLATE_PATH), curr_dir)

        paper_global_config = paper_global_tpl.as_dict()
        paper_global_config["proxies"]["velocity"][
            "secret"
        ] = velocity_forwarding_secret

        self.write_config(
            paper_global_yml_path,
            paper_global_config,
            (
                "#\n"
                "# This file is largely unmodified from paper defaults except for proxies.velocity values.\n"
                "# Particularly, proxies.velocity.secret is set to the value in our velocity secrets file."
                "#\n\n"
            ),
            YamlConfig.write_cb,
        )

    def merge_fabric_forge_prereq_mods(self):
        pass
