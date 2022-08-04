import json
import re

from pprint import pformat
from functools import total_ordering
from pathlib import Path
from typing import Callable, List, Optional

from src.api.constants import ENV_FOLDER
from src.common.logger_setup import logger


@total_ordering
class Env:
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
            entries.append(f" {field}: '{getattr(self, field)}'")

        return "{" + ",".join(entries) + "}"

    def toJson(self):
        return {field: getattr(self, field) for field in self.fields_to_print}

    fields_to_print = [
        "name",
        "alias",
        "type",
        "num",
        "formatted",
    ]

    name: str
    alias: str

    type: str
    num: Optional[int]

    formatted: str


def is_env_valid(env_name: str):
    env_file_path = ENV_FOLDER / f"{env_name}.toml"
    return env_file_path.exists()


def ensure_valid_env(func: Callable):
    def wrapper(*args, **kwargs):
        if "env" not in kwargs:
            raise Exception("Must pass an 'env' arg to this function call!")

        env_name = kwargs["env"]
        if not is_env_valid(env_name):
            raise Exception(
                f"Tried to run a command on an environment that does not exist! Got: '{env}'"
            )
        return func(*args, **kwargs)

    return wrapper


def get_env_alias_from_config(env: str):
    return env


def list_valid_envs() -> List[Env]:
    envs = []

    for item in ENV_FOLDER.iterdir():
        if item.is_dir():
            continue
        elif item.suffix != ".toml":
            continue

        env = Env()

        name = item.stem
        env.name = name
        env.alias = get_env_alias_from_config(name)

        env.type = re.sub(r"\d", "", name)
        num = re.sub(r"\D", "", name)
        env.num = int(num) if num != "" else None

        env.formatted = f"{env.type.capitalize()}"
        if env.num is not None:
            env.formatted += f" {env.num}"

        envs.append(env)

    # Doesn't matter in backend world but does in frontend.
    return sorted(envs)
