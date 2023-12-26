#!/bin/env python3

import os
import pwd
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
    MINECRAFT_UID = None
    MINECRAFT_GID = None

    container_name_label = "net.yukkuricraft.container_name"
    container_type_label = "net.yukkuricraft.container_type"
    docker_compose_template: YamlConfig

    generated_docker_compose_name: str
    generated_docker_compose: dict = {}

    container_name_format = "YC-{env}-{name}"

    WORLDGROUP_NAME_BLOCKLIST = [
        "defaultconfigs", # :`) Ugly folder structures yay`
    ]

    def __init__(self, env: str):
        super().__init__(env)

        uid = os.getuid()
        user = pwd.getpwuid(uid)
        self.MINECRAFT_UID = user.pw_name
        self.MINECRAFT_GID = user.pw_gid

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
        for world in self.get_enabled_world_groups():
            world_log_path = container_logs_path / self.env / "worlds" / world

            logger.info(f"CREATING PREREQ DIRECTORY {world_log_path}")
            world_log_path.mkdir(parents=True, exist_ok=True)
        # Recursively chown the base path for container logs to group minecraft
        recursive_chown(container_logs_path, None, self.MINECRAFT_GID)

    def get_generated_docker_compose_path(self):
        return self.generated_docker_compose_folder / self.generated_docker_compose_name

    def add_host_and_container_names(self):
        for service_key, service in self.generated_docker_compose["services"].items():
            name = service["labels"][self.container_name_label]
            container_name = self.container_name_format.format(env=self.env, name=name)

            logger.info(container_name)
            service["container_name"] = container_name
            service["hostname"] = container_name

            self.generated_docker_compose["services"][service_key] = service
            logger.info(service)

    def generate_velocity_service_config(self):
        velocity_service = (
            self.docker_compose_template.custom_extensions.velocity_template.as_dict()
        )
        for world in self.get_enabled_world_groups():
            velocity_service["depends_on"][f"mc_{world}"] = {
                'condition': 'service_healthy'
            }
        self.generated_docker_compose["services"]["velocity"] = velocity_service


    def generate_minecraft_service_config(self):
        services = self.generated_docker_compose["services"]
        # Add minecraft services
        for world in self.get_enabled_world_groups():
            mc_service_template = copy.deepcopy(
                self.docker_compose_template.custom_extensions.mc_service_template.as_dict()
            )
            mc_service_template = self.replace_interpolations(mc_service_template, world)
            mc_service_template["labels"][self.container_name_label] = world
            mc_service_key = f"mc_{world}"
            services[mc_service_key] = mc_service_template

            if self.is_prod() or self.env_config["general"].get_or_default("enable_backups", None):
                backup_service_template = copy.deepcopy(
                    self.docker_compose_template.custom_extensions.mc_backups_sidecar_template.as_dict()
                )
                backup_service_template = self.replace_interpolations(backup_service_template, world)
                backup_service_template["environment"]["RCON_HOST"] = self.container_name_format.format(env=self.env, name=world)
                backup_service_template["labels"][self.container_name_label] = f"{world}_backup"
                backup_service_template["depends_on"][mc_service_key] = {
                    'condition': 'service_healthy'
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

        for world in self.get_enabled_world_groups():
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
        # Add version
        self.generated_docker_compose["version"] = self.docker_compose_template.version

        self.generated_docker_compose["services"] = self.docker_compose_template.services.as_dict()
        self.generate_velocity_service_config()
        self.generate_minecraft_service_config()

        self.generate_volumes()
        self.generate_networks()

    def dump_write_cb(self, f, config):
        f.write(
            yaml.safe_dump(
                config,
                default_flow_style=False,
                sort_keys=False,
            )
        )

    def dump_generated_docker_compose(self):
        generated_docker_compose_path = self.get_generated_docker_compose_path()

        self.write_config(
            generated_docker_compose_path,
            self.generated_docker_compose,
            "#\n# THIS FILE IS AUTOMATICALLY GENERATED.\n# CHANGES WILL BE OVERWRITTEN ON RESTART.\n#\n\n",
            self.dump_write_cb
        )
        print("Done.")

    def run(self):
        self.generate_prereqs()
        self.generate_docker_compose()
        self.add_host_and_container_names()
        self.dump_generated_docker_compose()
