from pathlib import Path
from typing import Callable


ENV_FOLDER: Path = Path("/app/env")


class Environment:
    @staticmethod
    def is_env_valid(env: str):
        env_file_path = ENV_FOLDER / f"{env}.toml"
        return env_file_path.exists()

    @staticmethod
    def ensure_valid_env(func: Callable):
        """
        Decorated function must take a named arg called 'env'
        """

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

    # TODO: Env creation

    def create_new_dev_env(self, name: str):
        pass
