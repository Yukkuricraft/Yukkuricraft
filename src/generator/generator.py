#!/bin/env python3

import enum

from src.common.environment import Env

from src.generator.docker_compose_gen import DockerComposeGen
from src.generator.velocity_config_gen import VelocityConfigGen
from src.generator.new_dev_env_gen import NewDevEnvGen
from src.generator.env_file_gen import EnvFileGen


class GeneratorType(enum.Enum):
    DOCKER_COMPOSE = 1
    VELOCITY_CONFIG = 2
    NEW_DEV_ENV = 3
    ENV_FILE = 4


def get_generator(gen_type: GeneratorType, env: Env):
    if gen_type == GeneratorType.DOCKER_COMPOSE:
        return DockerComposeGen(env)
    elif gen_type == GeneratorType.VELOCITY_CONFIG:
        return VelocityConfigGen(env)
    elif gen_type == GeneratorType.NEW_DEV_ENV:
        return NewDevEnvGen(env)
    elif gen_type == GeneratorType.ENV_FILE:
        return EnvFileGen(env)
