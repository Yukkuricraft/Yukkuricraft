import json
import time
import shutil
import docker
from docker.models.containers import Container

from pathlib import Path
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

    def list_backups_by_env_and_tags(self, env: Env, tags: List[str]):
        env = env.name

        tags_str = (
            ''
            if not tags
            else f"--tag {','.join(tags)}"
        )

        response_as_json = self.docker_client.containers.run(
            image="restic/restic",
            command=f"snapshots --json {tags_str}",
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

        return backups

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
            else "bash /restic.sh backup" # Just performs the restic command directly
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
                # Use explicit volumes instead of volumes_from as the target container name may not be up if compose cluster is down.
                f"{RESTIC_REPO_PATH}:/backups",
                f"{ServerPaths.get_data_dir_path(env.name, world_group, DataDirType.WORLD_FILES)}:/worlds-bindmount",
                f"{ServerPaths.get_restic_password_file_path()}:/restic.password",
                f"{ServerPaths.get_rcon_password_file_path()}:/rcon.password",
            ],
            network=(
                f"{env.name}_ycnet"
                if mc_container_up
                else ""
            )
        )
        return out_b.decode("utf-8")

    def archive_directory(self, dir_to_archive: Path, archive_dir_suffix: str = "_archives", max_archives = 10):
        """Archives the `dir_to_archive` dir.

        - The name of the archive dir will be of format f"{dir_to_archive}{archive_dir_suffix}".
        - The directory being archived will have the current epoch timestamp appended to it.

        If `dir_to_archive` is `/a/b/c` and `archive_dir_suffic` is `_archive`, the archived directory
            will exist in `/a/b/c_archive/c-123456789`

        NOTE: This method is naive in a few ways:
        - We assume all dirs/files in the archive directory are archives of our target dir to archive.
          - If we have two types of archives in the same dir, our "max archives" logic will fail

        Args:
            dir_to_archive (Path): Directory to archive
            archive_dir_suffix (str): Suffix of the archive dir.
            max_archives (int): Maximum number of archived directories. Will remove oldest after this # is reached.
        """
        archive_dir = Path(f"{str(dir_to_archive)}{archive_dir_suffix}")
        if not archive_dir.exists():
            archive_dir.mkdir()

        existing_archives = [ path for path in archive_dir.iterdir() if path.is_dir() ]
        if len(existing_archives) >= max_archives:
            sorted_archives = sorted(existing_archives)
            num_to_delete = max(0, len(existing_archives) - max_archives + 1) # +1 because we're about to archive the curr dir too.

            # We naively assume all items in the sorted archives dir are archives that have the same format as each other,
            # thus doing a naive sort will sort the archives by age (epoch timestamp).
            archives_to_delete = sorted_archives[:num_to_delete]
            for archive in archives_to_delete:
                logger.info(f">> Deleting old archive! '{archive}'")
                shutil.rmtree(archive)

        logger.info(f">> Archiving directory '{dir_to_archive}'")
        new_archive_name = f"{dir_to_archive.name}-{int(time.time())}"
        archive_destination = archive_dir / new_archive_name

        logger.info(f">> Archiving directory '{dir_to_archive}' -> '{archive_destination}'")
        dir_to_archive.rename(archive_destination)


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

        world_files_dir = ServerPaths.get_data_dir_path(env.name, world_group, DataDirType.WORLD_FILES)

        self.archive_directory(
            world_files_dir,
        )

        out_b = self.docker_client.containers.run(
            name=restore_container_name,
            image="restic/restic",
            command=f"restore {target_id} --target /",
            remove=True,
            environment={
                "RESTIC_REPOSITORY": "/backups",
                "RESTIC_PASSWORD_FILE": "/restic.password",
            },
            volumes=[
                f"{RESTIC_REPO_PATH}:/backups",
                f"{world_files_dir}:/worlds-bindmount",
                f"{ServerPaths.get_restic_password_file_path()}:/restic.password",
            ],
        )

        logger.info(out_b)

        return out_b.decode("utf-8")