import json
import re

from pprint import pformat
from functools import total_ordering
from pathlib import Path
from typing import Callable, List, Optional

from src.api.constants import ENV_FOLDER, MIN_VALID_PROXY_PORT, MAX_VALID_PROXY_PORT
from src.api.lib.runner import Runner
from src.common.config import load_toml_config
from src.common.logger_setup import logger
from src.generator.generator import GeneratorType, get_generator


@total_ordering
class Env:
    @classmethod
    def from_env_string(cls, env_str: str):
        envs = list_valid_envs()
        for env in envs:
            if env.name == env_str:
                return env

        return None

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        # Do we want to support non-prod/dev envs in the future?
        if self.name == "prod":
            return True

        return self.name < other.name

    def __repr__(self):
        entries = []
        for field in self.fields_to_print:
            entries.append(f" {field}: '{pformat(getattr(self, field))}'")

        return "{" + ",".join(entries) + "}"

    def toJson(self):
        return {field: getattr(self, field) for field in self.fields_to_print}

    fields_to_print = [
        "type",
        "num",
        "config",
        "name",
        "description",
        "alias",
        "formatted",
    ]

    type: str
    num: Optional[int]

    config: dict

    name: str
    description: str
    alias: str
    formatted: str


def env_str_to_toml_path(env_str: str):
    return ENV_FOLDER / f"{env_str}.toml"


def is_env_valid(env_str: str):
    return env_str_to_toml_path(env_str).exists()


def ensure_valid_env(func: Callable):
    def wrapper(*args, **kwargs):
        if "env" not in kwargs:
            raise Exception(
                "Must pass an explicitly named 'env' arg to this function call! Eg, func_call(env=env)"
            )

        env_name = kwargs["env"]
        if not is_env_valid(env_name):
            raise Exception(
                f"Tried to run a command on an environment that does not exist! Got: '{env}'"
            )
        return func(*args, **kwargs)

    return wrapper


def _load_runtime_env_var(env_str: str, env_var: str):
    config = load_toml_config(env_str_to_toml_path(env_str), no_cache=True)
    env_vars = config["runtime-environment-variables"]
    if not env_vars:
        raise Exception("Invalid Env Config...?")

    return env_vars[env_var] if env_var in env_vars else env_str


def get_env_alias_from_config(env_str: str):
    return _load_runtime_env_var(env_str, "ENV_ALIAS")


def get_proxy_port_from_config(env_str: str):
    return _load_runtime_env_var(env_str, "VELOCITY_PORT")


def get_config_dict_from_config(env_str: str):
    return {
        "proxy_port": _load_runtime_env_var(env_str, "VELOCITY_PORT"),
        "server_type": _load_runtime_env_var(env_str, "MC_TYPE"),
        "server_build": _load_runtime_env_var(env_str, "PAPER_BUILD"),
        "mc_version": _load_runtime_env_var(env_str, "MC_VERSION"),
        "fs_root": _load_runtime_env_var(env_str, "MC_FS_ROOT"),
    }


def get_env_desc_from_config(env_str: str):
    config = load_toml_config(env_str_to_toml_path(env_str), no_cache=True)
    general = config["general"] if "general" in config else {}

    return general["description"] if "description" in general else ""


def get_next_valid_dev_env_number():
    """
    Starts checking from dev1, dev2, etc.
    Returns the next valid int.

    Will not check for any numbers that skip
    Eg having dev1, dev2, dev666 will return dev3.
    """

    next_valid_dev_env_number = 1
    dev_envs = list(filter(lambda env: env.type == "dev", list_valid_envs()))
    dev_envs.sort(key=lambda env: env.num)
    for env in dev_envs:
        if env.num == next_valid_dev_env_number:
            next_valid_dev_env_number += 1

    return next_valid_dev_env_number


def list_valid_envs() -> List[Env]:
    envs = []

    for item in ENV_FOLDER.iterdir():
        if item.is_dir():
            continue
        elif item.suffix != ".toml":
            continue

        env = Env()

        name = item.stem

        env.type = re.sub(r"\d", "", name)
        num = re.sub(r"\D", "", name)
        env.num = int(num) if num != "" else None

        env.config = get_config_dict_from_config(name)

        env.name = name
        env.description = get_env_desc_from_config(name)
        env.alias = get_env_alias_from_config(name)
        env.formatted = f"{env.type.capitalize()}"

        if env.num is not None:
            env.formatted += f" {env.num}"

        envs.append(env)

    # Sorting doesn't matter in backend world but does in frontend.
    rtn = sorted(envs, key=lambda d: d.name)
    if rtn[-1].name == "prod":
        # We really shouldn't ever have anything other than one prod and n dev_n's with aliases.
        rtn.insert(0, rtn.pop(-1))
    logger.info(f"??? SORTED ENVS: {rtn}")
    return rtn


def create_new_env(proxy_port: int, env_alias: str = "", description: str = ""):
    if proxy_port < MIN_VALID_PROXY_PORT or proxy_port > MAX_VALID_PROXY_PORT:
        raise Exception(
            f"Invalid proxy port supplied. Must be between {MIN_VALID_PROXY_PORT} and {MAX_VALID_PROXY_PORT}"
        )

    env_name = f"dev{get_next_valid_dev_env_number()}"

    # Generate env toml config
    gen = get_generator(GeneratorType.NEW_DEV_ENV, "prod")  # Configurable?
    gen.run(env_name, proxy_port, env_alias, description)

    # Generate docker compose file
    gen = get_generator(GeneratorType.DOCKER_COMPOSE, env_name)
    gen.run()

    # Generate velocity file
    gen = get_generator(GeneratorType.VELOCITY_CONFIG, env_name)
    gen.run()

    return {}, env_name


def delete_dev_env(env: str):
    cmd = ["make", "delete_env", env]
    logger.info("DELETING ENV: ", env)
    return Runner.run_make_cmd(cmd, env=env)
