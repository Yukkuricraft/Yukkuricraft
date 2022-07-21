import json

from pathlib import Path
from typing import Callable, List

from src.api.constants import ENV_FOLDER


def is_env_valid(env: str):
    env_file_path = ENV_FOLDER / f"{env}.toml"
    return env_file_path.exists()


def ensure_valid_env(func: Callable):
    def wrapper(*args, **kwargs):
        if "env" not in kwargs:
            raise Exception("Must pass an 'env' arg to this function call!")

        env = kwargs["env"]
        if not is_env_valid(env):
            raise Exception(
                f"Tried to run a command on an environment that does not exist! Got: '{env}'"
            )
        return func(*args, **kwargs)

    return wrapper


def list_valid_envs() -> List[str]:
    env_files = []

    for item in ENV_FOLDER.iterdir():
        if item.is_dir():
            continue
        elif item.suffix != ".toml":
            continue

        env_files.append(item.stem)

    return env_files
