import shutil
from typing import Callable, List, Optional

from src.api.constants import MIN_VALID_PROXY_PORT, MAX_VALID_PROXY_PORT

from src.common.environment import Env, InvalidPortException
from src.common.helpers import log_exception
from src.common.logger_setup import logger
from src.common import server_paths

from src.common import server_type_actions
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


def list_valid_envs(as_obj=True) -> List[Env | str]:
    """Returns a list of valid and defined `Env`s in the `env/` folder

    Args:
        as_obj(bool): Return as `Env`s if True (default), else as strings

    Returns:
        List[Env|str]: List of valid envs where type depends on `as_obj`
    """
    envs = []

    for item in server_paths.get_env_toml_config_dir_path().iterdir():
        if item.is_dir():
            continue
        elif item.suffix != ".toml":
            continue
        if not Env.is_valid_env(item.stem):
            continue

        try:
            envs.append(Env(item.stem) if as_obj else item)
        except Exception:
            log_exception()

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
        server_type (str): Server type use. Will be set as `cluster-variables.MC_TYPE`
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


def delete_env(env_str: str):
    """Delete an environment defined by its env string

    Cannot delete some envs such as env1.

    Args:
        env (str): Environment name string

    """

    if env_str == "env1":
        # Do we want to explicitly keep denying env1 dleetions?
        return False

    # Delete BASE_DATA_DIR
    base_data_dir = server_paths.get_env_data_path(env_str)
    logger.info(f"Deleting {base_data_dir}...")
    shutil.rmtree(str(base_data_dir), ignore_errors=True)

    # Delete env toml
    env_toml = server_paths.get_env_toml_config_path(env_str)
    logger.info(f"Deleting {env_toml}...")
    env_toml.unlink(missing_ok=True)

    # Delete Velocity config
    velocity_config = server_paths.get_generated_velocity_config_path(env_str)
    logger.info(f"Deleting {velocity_config}...")
    velocity_config.unlink(missing_ok=True)

    # Delete docker compose file
    docker_compose = server_paths.get_generated_docker_compose_path(env_str)
    logger.info(f"Deleting {docker_compose}...")
    docker_compose.unlink(missing_ok=True)

    return True


def generate_env_configs(env: Env):
    generate_all(env)

    return {}


def generate_all(env: Env):
    # Generate env file
    gen = get_generator(GeneratorType.ENV_FILE, env)
    gen.run()

    gen = get_generator(GeneratorType.WORLD_GROUPS_FILE_GEN, env)
    gen.run()

    generate_velocity_and_docker(env)

    server_type_actions.write_fabric_proxy_files(env)


def generate_velocity_and_docker(env: Env):
    # Generate docker compose file
    gen = get_generator(GeneratorType.DOCKER_COMPOSE, env)
    gen.run()

    # Generate velocity file
    gen = get_generator(GeneratorType.VELOCITY_CONFIG, env)
    gen.run()
