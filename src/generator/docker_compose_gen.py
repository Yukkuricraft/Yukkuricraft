#!/bin/env python3

import os
import pwd
import copy

from pathlib import Path
from src.common.config.config_node import ConfigNode
from src.common import server_paths

from src.generator.constants import (
    DOCKER_COMPOSE_TEMPLATE_PATH,
)

from src.common.constants import (
    YC_CONTAINER_NAME_LABEL,
)
from src.common.environment import Env

from src.generator.base_generator import BaseGenerator
from src.common.config import YamlConfig, load_yaml_config
from src.common.constants import MC_DOCKER_CONTAINER_NAME_FMT
from src.common.logger_setup import logger

WORLD_GROUP_INTERP_STR = "<<WORLDGROUP>>"


class DockerComposeGen(BaseGenerator):
    minecraft_uid = None
    minecraft_gid = None

    docker_compose_template: YamlConfig

    generated_docker_compose_name: str
    generated_docker_compose: dict = {}

    def __init__(self, env: Env):
        super().__init__(env)

        uid = os.getuid()
        user = pwd.getpwuid(uid)
        self.minecraft_uid = user.pw_name
        self.minecraft_gid = user.pw_gid

        self.generated_docker_compose_path = (
            server_paths.get_generated_docker_compose_path(self.env.name)
        )
        if not self.generated_docker_compose_path.parent.exists():
            self.generated_docker_compose_path.parent.mkdir(parents=True)

        curr_dir = Path(__file__).parent
        self.docker_compose_template = load_yaml_config(
            curr_dir / DOCKER_COMPOSE_TEMPLATE_PATH, no_cache=True
        )

    def add_host_and_container_names(self):
        for service_key, service in self.generated_docker_compose["services"].items():
            name = service["labels"][YC_CONTAINER_NAME_LABEL]
            container_name = MC_DOCKER_CONTAINER_NAME_FMT.format(
                env=self.env.name, name=name
            )

            service["container_name"] = container_name
            service["hostname"] = container_name

            self.generated_docker_compose["services"][service_key] = service

    def generate_velocity_service_config(self):
        velocity_service = (
            self.docker_compose_template.custom_extensions.velocity_template.as_dict()
        )
        for world in self.env.world_groups:
            velocity_service["depends_on"][f"mc_{world}"] = {
                "condition": "service_healthy"
            }
        self.generated_docker_compose["services"]["velocity"] = velocity_service

    def generate_minecraft_service_config(self):
        services = self.generated_docker_compose["services"]
        # Add minecraft services
        for world in self.env.world_groups:
            mc_service_template = copy.deepcopy(
                self.docker_compose_template.custom_extensions.mc_service_template.as_dict()
            )
            mc_service_template = self.replace_interpolations(
                mc_service_template, WORLD_GROUP_INTERP_STR, world
            )

            docker_overrides = self.env.config.world_groups[world]
            for section_name in docker_overrides.listnodes():
                section_data = self.env.config.world_groups[world][section_name]

                if isinstance(section_data, ConfigNode):
                    for key, val in section_data.items():
                        mc_service_template[section_name][key] = val
                elif isinstance(section_data, list):
                    if section_name not in mc_service_template:
                        mc_service_template[section_name] = []
                    mc_service_template[section_name].extend(section_data)
                else:
                    mc_service_template[section_name] = section_data

            jmx_port = docker_overrides.environment.get("JMX_PORT", None)
            if jmx_port is not None:
                if "ports" not in mc_service_template:
                    mc_service_template["ports"] = []
                mc_service_template["ports"].append(f"{jmx_port}:{jmx_port}")

            mc_service_key = f"mc_{world}"
            services[mc_service_key] = mc_service_template

            if self.env.is_prod() or self.env.config.general.get(
                "enable_backups", None
            ):
                backup_service_template = copy.deepcopy(
                    self.docker_compose_template.custom_extensions.mc_backups_sidecar_template.as_dict()
                )
                backup_service_template = self.replace_interpolations(
                    backup_service_template, WORLD_GROUP_INTERP_STR, world
                )
                backup_service_template["environment"][
                    "RCON_HOST"
                ] = MC_DOCKER_CONTAINER_NAME_FMT.format(env=self.env.name, name=world)
                backup_service_template["depends_on"][mc_service_key] = {
                    "condition": "service_healthy"
                }
                backup_service_template["volumes_from"] = [f"{mc_service_key}:ro"]
                services[f"mc_{world}_backup"] = backup_service_template

    def generate_volumes(self):
        # Add volumes
        volumes = (
            self.docker_compose_template.volumes.as_dict()
            if self.docker_compose_template.volumes is not None
            else {}
        )

        volumes[f"velocity-{self.env.name}"] = None
        volumes[f"dbdata-{self.env.name}"] = None
        volumes[f"html-{self.env.name}"] = None
        volumes[f"vhost-{self.env.name}"] = None
        volumes[f"acme-{self.env.name}"] = None
        volumes[f"certs-{self.env.name}"] = {
            "driver": "local",
            "driver_opts": {
                "type": "none",
                "o": "bind",
                "device": f"{self.env.cluster_vars.MC_FS_ROOT}/env/{self.env.name}/certs",
            },
        }

        for world in self.env.world_groups:
            volumes[f"mcdata_{world}"] = None
            volumes[f"ycworldsvolume_{world}"] = None
            volumes[f"ycpluginsvolume_{world}"] = None

        self.generated_docker_compose["volumes"] = volumes

    def generate_networks(self):
        # Add networks
        networks = (
            self.docker_compose_template.networks.as_dict()
            if self.docker_compose_template.networks is not None
            else {}
        )

        self.generated_docker_compose["networks"] = networks

    def generate_docker_compose(self):
        self.generated_docker_compose[
            "services"
        ] = self.docker_compose_template.services.as_dict()
        self.generate_velocity_service_config()
        self.generate_minecraft_service_config()

        self.generate_volumes()
        self.generate_networks()

    def dump_generated_docker_compose(self):

        self.write_config(
            self.generated_docker_compose_path,
            self.generated_docker_compose,
            YamlConfig.write_cb,
            "#\n# THIS FILE IS AUTOMATICALLY GENERATED.\n# CHANGES WILL BE OVERWRITTEN ON RESTART.\n#\n\n",
        )
        logger.info("Done.")

    def run(self):
        self.generate_docker_compose()
        self.add_host_and_container_names()
        self.dump_generated_docker_compose()
