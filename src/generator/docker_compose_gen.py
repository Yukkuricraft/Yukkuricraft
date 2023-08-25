#!/bin/env python3

import os
import copy
import yaml  # type: ignore

yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
)

from typing import Dict
from pathlib import Path
from pprint import pformat

from src.generator.constants import (
    DOCKER_COMPOSE_TEMPLATE_NAME,
    DEFAULT_CHMOD_MODE,
)

from src.generator.base_generator import BaseGenerator
from src.common.config import YamlConfig, load_yaml_config
from src.common.logger_setup import logger
from src.common.helpers import recursive_chown


class DockerComposeGen(BaseGenerator):
    MINECRAFT_UID = 1000 # Hm...
    MINECRAFT_GID = 1000

    container_name_label = "net.yukkuricraft.container_name"
    container_type_label = "net.yukkuricraft.container_type"
    docker_compose_template: YamlConfig

    generated_docker_compose_name: str
    generated_docker_compose: dict = {}

    def __init__(self, env: str):

        super().__init__(env)

        self.generated_docker_compose_name = f"docker-compose-{self.env}.yml"
        self.generated_docker_compose_folder = (
            Path(__file__).parent.parent.parent / "gen"
        )  # G w o s s

        if not self.generated_docker_compose_folder.exists():
            self.generated_docker_compose_folder.mkdir()

        curr_dir = Path(__file__).parent
        self.docker_compose_template = load_yaml_config(
            DOCKER_COMPOSE_TEMPLATE_NAME, curr_dir
        )

    def generate_prereqs(self):
        container_logs_path = Path("container_logs")

        # Generate log paths to mount into containers
        for world in self.env_config["world-groups"].enabled_groups:
            world_log_path = container_logs_path / self.env / "worlds" / world

            logger.info(f"CREATING PREREQ DIRECTORY {world_log_path}")
            world_log_path.mkdir(parents=True, exist_ok=True)
        # Recursively chown the base path for container logs to group minecraft
        recursive_chown(container_logs_path, None, self.MINECRAFT_GID)

    def get_generated_docker_compose_path(self):
        return self.generated_docker_compose_folder / self.generated_docker_compose_name

    def generate_docker_compose(self):
        services = self.docker_compose_template.services.as_dict()

        # Add version
        self.generated_docker_compose["version"] = self.docker_compose_template.version

        # Add velocity service
        velocity_service = (
            self.docker_compose_template.custom_extensions.velocity_template.as_dict()
        )
        for world in self.env_config["world-groups"].enabled_groups:
            velocity_service["depends_on"][f"mc_{world}"] = {
                'condition': 'service_healthy'
            }

        services["velocity"] = velocity_service

        # Add minecraft services

        for world in self.env_config["world-groups"].enabled_groups:
            service_template = copy.deepcopy(
                self.docker_compose_template.custom_extensions.mc_service_template.as_dict()
            )
            service_template = self.replace_interpolations(service_template, world)

            # Using the generated name (when no container_name is supplied) or config object name (eg, "mc_survival"), Velocity isn't able to
            #     resolve the supplied alias. For whatever reason, explicitly declared container_names do work, however.
            service_template["container_name"] = f"YC-{world}-{self.env}"
            service_template["labels"][self.container_name_label] = world

            services[f"mc_{world}"] = service_template
        self.generated_docker_compose["services"] = services

        # Add volumes
        volumes = (
            self.docker_compose_template.volumes.as_dict()
            if self.docker_compose_template.volumes is not None
            else {}
        )

        volumes[f"velocity-{self.env}"] = None
        volumes[f"dbdata-{self.env}"] = None
        volumes[f"html-{self.env}"] = None
        volumes[f"vhost-{self.env}"] = None
        volumes[f"acme-{self.env}"] = None
        volumes[f"certs-{self.env}"] = {
            "driver": "local",
            "driver_opts": {
                "type": "none",
                "o": "bind",
                "device": f"{self.env_config['runtime-environment-variables'].MC_FS_ROOT}/env/{self.env}/certs",
            },
        }

        for world in self.env_config["world-groups"].enabled_groups:
            volumes[f"mcdata_{world}"] = None
            volumes[f"ycworldsvolume_{world}"] = None
            volumes[f"ycpluginsvolume_{world}"] = None

        self.generated_docker_compose["volumes"] = volumes

        # Add networks
        networks = (
            self.docker_compose_template.networks.as_dict()
            if self.docker_compose_template.networks is not None
            else {}
        )
        # networks[f"ycnet-{self.env}"] = None

        self.generated_docker_compose["networks"] = networks

    def dump_generated_docker_compose(self):
        generated_docker_compose_path = self.get_generated_docker_compose_path()
        with open(generated_docker_compose_path, "w") as f:
            f.write(
                "#\n# THIS FILE IS AUTOMATICALLY GENERATED.\n# CHANGES WILL BE OVERWRITTEN ON RESTART.\n#\n\n"
            )
            f.write(
                yaml.safe_dump(
                    self.generated_docker_compose,
                    default_flow_style=False,
                    sort_keys=False,
                )
            )
        os.chmod(generated_docker_compose_path, DEFAULT_CHMOD_MODE)
        print("Done.")

    def run(self):
        self.generate_prereqs()
        self.generate_docker_compose()
        self.dump_generated_docker_compose()
