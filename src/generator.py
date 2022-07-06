#!/bin/env python3

import copy
import yaml # type: ignore

yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:null', '')
)

from src.constants import DOCKER_COMPOSE_TEMPLATE_NAME, CONFIG_NAME
from src.common.config import Config, get_config

class Generator:
    config: Config
    docker_compose_template: Config

    generated_config: dict = {}

    def __init__(self):
        self.config = get_config(CONFIG_NAME)
        self.docker_compose_template = get_config(DOCKER_COMPOSE_TEMPLATE_NAME)

    def replace_interpolations(self, inp, replace_value: str):
        """
        Please for the love of god refactor me in the future.
        """
        if type(inp) == list:
            return [ self.replace_interpolations(item, replace_value) for item in inp ]
        elif type(inp) == dict:
            return {
                self.replace_interpolations(key, replace_value): self.replace_interpolations(value, replace_value)
                for key, value in inp.items()
            }
        elif type(inp) == str:
            return inp.replace("<<WORLDGROUP>>", replace_value)
        else:
            return inp

    def generate_config(self):

        # Add version
        self.generated_config['version'] = self.docker_compose_template.version

        # Add services
        services = self.docker_compose_template.services.as_dict()
        for world in self.config.world_groups:
            service_template = copy.deepcopy(self.docker_compose_template.custom_extensions.mc_service_template.as_dict())
            service_template = self.replace_interpolations(service_template, world)

            services[f"mc_{world}"] = service_template
        self.generated_config['services'] = services

        # Add volumes
        volumes = self.docker_compose_template.volumes.as_dict()
        for world in self.config.world_groups:
            volumes[f"mcdata_{world}"] = None
            volumes[f"ycworldsvolume_{world}"] = None
            volumes[f"ycpluginsvolume_{world}"] = None
        self.generated_config['volumes'] = volumes

        # Add networks
        self.generated_config['networks'] = self.docker_compose_template.networks.as_dict()

    def dump_config(self):
        print("Generating new docker-compose.yml...")
        with open("docker-compose.yml", "w") as f:
            f.write(yaml.safe_dump(self.generated_config, default_flow_style=False, sort_keys=False))
        print("Done.")

    def run(self):
        self.generate_config()
        self.dump_config()

