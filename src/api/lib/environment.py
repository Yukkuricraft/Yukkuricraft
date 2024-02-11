from typing import Callable, List, Optional

from src.api.constants import MIN_VALID_PROXY_PORT, MAX_VALID_PROXY_PORT
from src.api.lib.runner import Runner

from src.common.environment import Env, InvalidPortException
from src.common.logger_setup import logger
from src.common.paths import ServerPaths
from src.common.server_type_actions import ServerTypeActions

from src.generator.generator import GeneratorType, get_generator


def get_next_valid_env_number():
    """
    Starts checking from dev1, dev2, etc.
    Returns the next valid int.

    Will not check for any numbers that skip
    Eg having dev1, dev2, dev666 will return dev3.
    """

    next_valid_env_number = 1
    envs = list_valid_envs()
    envs.sort(key=lambda env: env.num)
    for env in envs:
        if env.num == next_valid_env_number:
            next_valid_env_number += 1

    return next_valid_env_number


def list_valid_envs(as_obj = True) -> List[Env|str]:
    """Returns a list of valid and defined `Env`s in the `env/` folder

    Args:
        as_obj(bool): Return as `Env`s if True (default), else as strings

    Returns:
        List[Env|str]: List of valid envs where type depends on `as_obj`
    """
    envs = []

    for item in ServerPaths.get_env_toml_config_dir_path().iterdir():
        if item.is_dir():
            continue
        elif item.suffix != ".toml":
            continue
        if not Env.is_valid_env(item.stem):
            continue

        try:
            envs.append(Env(item.stem) if as_obj else item)
        except Exception as e:
            logger.warn(e)

    # Sorting doesn't matter in backend world but does in frontend.
    rtn = sorted(envs, key=lambda d: d.name)
    return rtn

def create_new_env(
    proxy_port: int,
    env_alias: str,
    enable_env_protection: bool,
    server_type: str,
    description: str = "",
) -> Env:
    """Creates a new env using the next available and valid env number.

    Args:
        proxy_port (int): Port to use for the proxy
        env_alias (str): Human readable alias (name) for this env
        enable_env_protection (bool): Whether to enable env protection, which disables deleting the env.
        server_type (str): Server type use. Will be set as `runtime-environment-variables.MC_TYPE`
        description (str, optional): Description for humans. Defaults to "".

    Raises:
        InvalidPortException: Invalid port

    Returns:
        Env: An Env object representing the new environment.
    """
    if proxy_port < MIN_VALID_PROXY_PORT or proxy_port > MAX_VALID_PROXY_PORT:
        raise InvalidPortException(
            f"Invalid proxy port supplied. Must be between {MIN_VALID_PROXY_PORT} and {MAX_VALID_PROXY_PORT}"
        )

    env_name = f"env{get_next_valid_env_number()}"

    # Generate env toml config
    gen = get_generator(GeneratorType.NEW_DEV_ENV, Env("env1"))  # Configurable?
    gen.run(
        env_name, proxy_port, env_alias, enable_env_protection, server_type, description
    )

    # Order matters. Can't instantiate Env() until config has been generated with above.
    env = Env(env_name)
    generate_velocity_and_docker(env)
    return env


def delete_dev_env(env_str: str):
    """Delete an environment defined by its env string

    Cannot delete some envs such as env1.

    Args:
        env (str): Environment name string

    Returns:
        _type_: _description_
    """
    cmd = ["make", "delete_env"]
    logger.info(f"DELETING ENV: {env_str}")
    return Runner.run_make_cmd(cmd, env=Env(env_str))


def generate_env_configs(env: Env):
    generate_all(env)

    ServerTypeActions().run(env)

    return {}


def generate_all(env: Env):
    # Generate env file
    gen = get_generator(GeneratorType.ENV_FILE, env)
    gen.run()
    generate_velocity_and_docker(env)


def generate_velocity_and_docker(env: Env):
    # Generate docker compose file
    gen = get_generator(GeneratorType.DOCKER_COMPOSE, env)
    gen.run()

    # Generate velocity file
    gen = get_generator(GeneratorType.VELOCITY_CONFIG, env)
    gen.run()
