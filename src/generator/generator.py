#!/bin/env python3

import enum

from src.generator.docker_compose_gen import DockerComposeGen
from src.generator.velocity_config_gen import VelocityConfigGen
from src.generator.new_dev_env_gen import NewDevEnvGen
from src.generator.env_file_gen import EnvFileGen


class GeneratorType(enum.Enum):
    DOCKER_COMPOSE = 1
    VELOCITY_CONFIG = 2
    NEW_DEV_ENV = 3
    ENV_FILE = 4


def get_generator(gen_type: GeneratorType, env: str):
    match gen_type:
        case GeneratorType.DOCKER_COMPOSE:
            return DockerComposeGen(env)
        case GeneratorType.VELOCITY_CONFIG:
            return VelocityConfigGen(env)
        case GeneratorType.NEW_DEV_ENV:
            return NewDevEnvGen(env)
        case GeneratorType.ENV_FILE:
            return EnvFileGen(env)
