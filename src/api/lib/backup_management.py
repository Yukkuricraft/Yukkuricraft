import json
import docker
from docker.models.containers import Container

from dataclasses import dataclass
from typing import List, Dict
from pprint import pformat

from src.api.lib.docker_management import DockerManagement
from src.api.lib.helpers import container_name_to_container
from src.common.logger_setup import logger
from src.common.environment import Env
from src.common.constants import HOST_REPO_ROOT_PATH, MC_DOCKER_CONTAINER_NAME_FMT, RESTIC_REPO_PATH
from src.common.paths import ServerPaths
from src.common.types import DataDirType


class InvalidContainerException(Exception):
    pass


class ContainerMissingEnvLabelException(InvalidContainerException):
    pass


class ContainerMissingNameLabelException(InvalidContainerException):
    pass


class CannotRestoreWhileContainerUpError(Exception):
    pass


class RestoreAlreadyInProgressError(Exception):
    pass


class BackupAlreadyInProgressError(Exception):
    pass


@dataclass
class Backup:
    excludes: List[str]
    gid: int
    hostname: str
    id: str
    parent: str
    paths: List[str]
    program_version: str
    short_id: str
    tags: List[str]
    time: str  # datetime?
    tree: str
    username: str


class BackupManagement:
    def __init__(self):
        self.docker_management = DockerManagement()
        self.docker_client = self.docker_management.client

    def container_name_to_container(self, container_name):
        return self.docker_client.containers.get(container_name)

    @staticmethod
    def contains_tags(backup: Dict, target_tags: List[str]) -> bool:
        if "tags" not in backup:
            return False

        for tag in target_tags:
            if tag not in backup["tags"]:
                return False

        return True

    def list_backups_by_env_and_tags(self, env: Env, tags: List[str]):
        env = env.name

        # Restic only supports logical ORs on the filters. Ie, can't do "env1 AND survival", only "env1 OR survival"
        # Filter out the results ourselves in python.
        response_as_json = self.docker_client.containers.run(
            image="restic/restic",
            command=f"snapshots --json",
            environment={
                "RESTIC_REPOSITORY": "/backups",
                "RESTIC_PASSWORD_FILE": "/restic.password",
            },
            volumes={
                str(RESTIC_REPO_PATH): {
                    "bind": "/backups",
                    "mode": "rw",
                },
                str(ServerPaths.get_restic_password_file_path()): {
                    "bind": "/restic.password",
                    "mode": "ro",
                },
            },
        )

        if isinstance(response_as_json, bytes):
            response_as_json = response_as_json.decode("utf-8")

        backups = json.loads(response_as_json)

        logger.info("RESPONSE FROM RESTIC SNAPSHOTS")
        logger.info(pformat(backups))

        return list(
            filter(lambda backup: BackupManagement.contains_tags(backup, tags), backups)
        )

    def backup_minecraft(self, env: Env, world_group: str):
        """Performs an ad-hoc backup of `world_group` in env `env`

        Args:
            env (Env): Target env to restore to
            world_group (str): The world to restore to, as referenced in world groups
            target_id (str): The restic backup id to restore from
        """

        mc_container_name = MC_DOCKER_CONTAINER_NAME_FMT.format(
            env=env.name,
            name=world_group,
        )


        backup_container_name = f"{mc_container_name}_backup_adhoc"
        if self.docker_management.is_container_up(backup_container_name):
            raise BackupAlreadyInProgressError(backup_container_name)

        mc_container_up = self.docker_management.is_container_up(mc_container_name)
        entrypoint_command = (
            "/usr/bin/backup now" # Performs rcon save-off/save-on
            if mc_container_up
            else "/scripts/restic.sh backup" # Just performs the restic command directly
        )

        logger.info(f"Backing up container for '{env.name}' '{world_group}' using '{backup_container_name}'")
        out_b = self.docker_client.containers.run(
            name=backup_container_name,
            image="yukkuricraft/mc-backup-restic",
            remove=True,
            environment={
                "BACKUP_NAME": f"{world_group}-adhoc",
                "BACKUP_METHOD": "restic",
                "SRC_DIR": "/worlds-bindmount",
                "RESTIC_REPOSITORY": "/backups",
                "RESTIC_PASSWORD_FILE": "/restic.password",
                "RESTIC_ADDITIONAL_TAGS": f"{env.name} {world_group} adhoc",
                "ENTRYPOINT_TARGET": entrypoint_command,
                "RESTIC_HOSTNAME": mc_container_name,
                "RCON_HOST": mc_container_name,
                "RCON_PASSWORD_FILE": "/rcon.password",
            },
            volumes=[
                f"{ServerPaths.get_data_dir_path(env.name, world_group, DataDirType.WORLD_FILES)}:/worlds-bindmount",
                f"{RESTIC_REPO_PATH}:/backups",
                #f"{ServerPaths.get_restic_password_file_path()}:/restic.password",
                #f"{ServerPaths.get_rcon_password_file_path()}:/rcon.password",
                "/home/remi/development/Yukkuricraft/secrets/restic.password:/restic.password",
                "/home/remi/development/Yukkuricraft/secrets/rcon.password:/rcon.password",
            ],
            network=(
                f"{env.name}_ycnet"
                if mc_container_up
                else "adhoc"
            )
        )
        return out_b.decode("utf-8")

    def restore_minecraft(self, env: Env, world_group: str, target_id: str):
        """Restores the `target_id` backup to `world_group` in env `env`

        Args:
            env (Env): Target env to restore to
            world_group (str): The world to restore to, as referenced in world groups
            target_id (str): The restic backup id to restore from
        """

        container_name = MC_DOCKER_CONTAINER_NAME_FMT.format(
            env=env.name,
            name=world_group,
        )

        if self.docker_management.is_container_up(container_name):
            raise CannotRestoreWhileContainerUpError(container_name)

        restore_container_name = f"{container_name}_restore"
        if self.docker_management.is_container_up(restore_container_name):
            raise RestoreAlreadyInProgressError(restore_container_name)

        out_b = self.docker_client.containers.run(
            name=restore_container_name,
            image="yukkuricraft/mc-backup-restic",
            remove=True,
            environment={
                "BACKUP_TARGET_ID": target_id,
                "BACKUP_DEST_PATH": "/worlds-bindmount",
                "RESTIC_REPOSITORY": "/backups",
                "RESTIC_PASSWORD_FILE": "/restic.password",
                "ENTRYPOINT_TARGET": "/scripts/restic.sh restore",
            },
            volumes=[
                f"{ServerPaths.get_data_dir_path(env.name, world_group, DataDirType.WORLD_FILES)}/remiliawashere:/worlds-bindmount",
                f"{ServerPaths.get_restic_password_file_path()}:/restic.password",
            ],
        )

        return out_b.decode("utf-8")