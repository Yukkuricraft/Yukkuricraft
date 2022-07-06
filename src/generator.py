#!/bin/env python3

from src.constants import DOCKER_COMPOSE_TEMPLATE_NAME, CONFIG_NAME
from src.common.config import Config, get_config

class Generator:
    config: Config
    docker_compose_template: Config

    def __init__(self):
        print("+++ Config")
        self.config = get_config(CONFIG_NAME)
        self.config.print_config()

        print("+++ Docker Compose Template")
        self.docker_compose_template = get_config(DOCKER_COMPOSE_TEMPLATE_NAME)
        self.docker_compose_template.print_config()

    def run(self):
        pass
