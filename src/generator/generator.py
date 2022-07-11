#!/bin/env python3

import enum

from src.generator.docker_compose_gen import DockerComposeGen
from src.generator.velocity_config_gen import VelocityConfigGen


class GeneratorType(enum.Enum):
    DOCKER_COMPOSE = 1
    VELOCITY_CONFIG = 2


def get_generator(gen_type: GeneratorType, env: str):
    if gen_type == GeneratorType.DOCKER_COMPOSE:
        return DockerComposeGen(env)
    if gen_type == GeneratorType.VELOCITY_CONFIG:
        return VelocityConfigGen(env)
