#!/bin/env python3

import os
import copy

from typing import Dict
from pathlib import Path

from src.generator.constants import (
    VELOCITY_CONFIG_TEMPLATE_PATH,
    DEFAULT_CHMOD_MODE,
)

from src.common.environment import Env

from src.generator.base_generator import BaseGenerator
from src.generator.docker_compose_gen import DockerComposeGen
from src.common.paths import ServerPaths
from src.common.config.toml_config import TomlConfig
from src.common.config import load_toml_config


class VelocityConfigGen(BaseGenerator):
    """
    TODO: Refactor to get more DRY between VelocityConfigGen and DockerComposeGen
    """

    velocity_config_template: TomlConfig

    generated_velocity_config_name: str
    generated_velocity_config: dict = {}

    def __init__(self, env: Env):

        super().__init__(env)

        self.generated_velocity_config_path = (
            ServerPaths.get_generated_velocity_config_path(env.name)
        )
        if not self.generated_velocity_config_path.parent.exists():
            self.generated_velocity_config_path.parent.mkdir()

        curr_dir = Path(__file__).parent
        self.velocity_config_template = load_toml_config(
            VELOCITY_CONFIG_TEMPLATE_PATH, curr_dir
        )

    def generate_velocity_config(self):

        # Copy baseline velocity config
        self.generated_velocity_config = self.velocity_config_template.as_dict()

        # Add servers and forced_hosts
        servers = {}
        forced_hosts = {}
        try_servers = []
        for world in self.env.world_groups:
            world_underscored = world.replace("-", "_")

            # Using the generated name (when no container_name is supplied) or config object name (eg, "mc_survival"), Velocity isn't able to
            #     resolve the supplied alias. For whatever reason, explicitly declared container_names do work, however.
            container_name = DockerComposeGen.container_name_format.format(
                env=self.env.name, name=world
            )
            servers[world_underscored] = f"{container_name}:25565"
            try_servers.append(world_underscored)

            if world == "lobby":
                # Allow both lobby.yukkuricraft.net as well as mc.yukkuricraft.net connect to the lobby.
                forced_hosts[f"mc.{self.env.hostname}"] = [world_underscored]
            forced_hosts[f"{world}.{self.env.hostname}"] = [world_underscored]

        servers["try"] = try_servers
        self.generated_velocity_config["servers"] = servers
        self.generated_velocity_config["forced-hosts"] = forced_hosts

    def dump_generated_velocity_config(self):
        print(f"Generating new {self.generated_velocity_config_path}...")

        self.write_config(
            self.generated_velocity_config_path,
            self.generated_velocity_config,
            "#\n# THIS FILE IS AUTOMATICALLY GENERATED.\n# CHANGES WILL BE OVERWRITTEN ON RESTART.\n#\n\n",
        )
        print("Done.")

    def run(self):
        self.generate_velocity_config()
        self.dump_generated_velocity_config()
