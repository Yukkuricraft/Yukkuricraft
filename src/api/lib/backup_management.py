import json
import time
import shutil

from pathlib import Path
from typing import Dict, List, Optional
from pprint import pformat
from unittest.mock import Mock

from docker import DockerClient

from src.api.constants import BACKUP_CONTENT_ROOT
from src.api.lib.docker_management import DockerManagement
from src.common.logger_setup import logger
from src.common.environment import Env
from src.common.constants import (
    MC_DOCKER_CONTAINER_NAME_FMT,
    RESTIC_REPO_PATH,
    HOST_UID,
    HOST_GID,
)
from src.common import server_paths
from src.common.types import DataDirType

from src.api.lib import (
    BackupAlreadyInProgressError,
    Backup,
    CannotRestoreWhileContainerUpError,
    RestoreAlreadyInProgressError,
)


class BackupManagement:
    docker_management: DockerManagement
    docker_client = DockerClient

    def __init__(self, docker_management: Optional[DockerManagement] = None):
        self.docker_management = (
            docker_management if docker_management is not None else DockerManagement()
        )
        self.docker_client = self.docker_management.client

    def call_restic(self, command: str, override_args: Optional[Dict] = None) -> str:
        override_args = override_args if override_args is not None else {}

        params = {
            "image": "restic/restic",
            "command": command,
            **override_args,
            "environment": {
                "RESTIC_REPOSITORY": "/backups",
                "RESTIC_PASSWORD_FILE": "/restic.password",
                **(override_args.get("environment", {})),
            },
            "volumes": {
                str(RESTIC_REPO_PATH): {
                    "bind": "/backups",
                    "mode": "rw",
                },
                str(server_paths.get_restic_password_file_path()): {
                    "bind": "/restic.password",
                    "mode": "ro",
                },
                **(override_args.get("volumes", {})),
            },
        }

        out = self.docker_client.containers.run(**params)
        if isinstance(out, bytes):
            out = out.decode("utf-8")

        return out

    def list_backups_by_env_and_tags(self, env: Env, tags: List[str]) -> List[Backup]:
        tags.append(env.name)
        tags_str = f"--tag {','.join(tags)}"

        response_as_json = self.call_restic(f"snapshots --json {tags_str}")

        if isinstance(response_as_json, bytes):
            response_as_json = response_as_json.decode("utf-8")

        logger.info("RESPONSE FROM RESTIC SNAPSHOTS")
        logger.info(pformat({"msg": "pre", "backups": response_as_json}))

        backups = json.loads(response_as_json)
        backups = list(map(lambda b: Backup(**b), backups))

        logger.info(pformat({"msg": "post", "backups": backups}))

        return backups

    def get_worlds_backed_up_in_snapshot(self, target_id: str):
        """Given a Restic snapshot id, gets the list of worlds that were backed up in that snapshot.

        We do this by looking at all directory names at the first depth after the backup root.

        Eg, a snapshot containing the following three files:
        - /worlds-bindmount/lobby/uid.dat
        - /worlds-bindmount/lobby_nether/uid.dat
        - /worlds-bindmount/lobby_nether/level.dat

        will be calculated as having the "lobby" and "lobby_nether" worlds in the snapshot as those are the directories
        at the first depth after the root (`/worlds-bindmount`)

        Args:
            target_id (str): Restic snapshot id

        Returns:
            _type_: _description_
        """
        worlds = set()

        response_as_json = self.call_restic(
            f"ls {target_id} {BACKUP_CONTENT_ROOT} --json "
        )
        # The output contains both the snapshot and file objects.
        for line in response_as_json.splitlines():
            d = json.loads(line)
            name = d.get("name")
            path = d.get("path")

            if path == BACKUP_CONTENT_ROOT:
                # Output contains the root dir as a file object.
                # If the object
                continue

            if name is not None:
                # We only want file objects.
                # Only file objects have the "name" field.
                worlds.add(name)

        return list(worlds)

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
            "/usr/bin/backup now"  # Performs rcon save-off/save-on
            if mc_container_up
            else "bash /restic.sh backup"  # Just performs the restic command directly
        )
        underscored_env_alias = env.alias.replace(" ", "_")

        logger.info(
            f"Backing up container for '{env.name}' '{world_group}' using '{backup_container_name}'"
        )
        logger.info(underscored_env_alias)
        out = self.docker_client.containers.run(
            name=backup_container_name,
            image="yukkuricraft/mc-backup-restic",
            remove=True,
            environment={
                "HOST_UID": HOST_UID,
                "HOST_GID": HOST_GID,
                "BACKUP_NAME": world_group,
                "BACKUP_METHOD": "restic",
                "SRC_DIR": BACKUP_CONTENT_ROOT,
                "RESTIC_REPOSITORY": "/backups",
                "RESTIC_PASSWORD_FILE": "/restic.password",
                "RESTIC_ADDITIONAL_TAGS": f"{env.name} adhoc {underscored_env_alias}",
                "ENTRYPOINT_TARGET": entrypoint_command,
                "RESTIC_HOSTNAME": mc_container_name,
                "RCON_HOST": mc_container_name,
                "RCON_PASSWORD_FILE": "/rcon.password",
                "PRUNE_BACKUPS_DAYS": "7",
                "PRUNE_RESTIC_RETENTION": "--keep-last 8 --keep-daily 7 --keep-weekly 8 --keep-monthly 24 --keep-yearly 666",
            },
            volumes=[
                # Use explicit volumes instead of volumes_from as the target container name may not be up if compose cluster is down.
                f"{RESTIC_REPO_PATH}:/backups",
                f"{server_paths.get_data_dir_path(env.name, world_group, DataDirType.WORLD_FILES)}:{BACKUP_CONTENT_ROOT}",
                f"{server_paths.get_restic_password_file_path()}:/restic.password",
                f"{server_paths.get_rcon_password_file_path()}:/rcon.password",
            ],
            network=(f"{env.name}_ycnet" if mc_container_up else ""),
        )

        if isinstance(out, bytes):
            out = out.decode("utf-8")

        return out

    def archive_directory(
        self,
        dir_to_archive: Path,
        archive_dir_suffix: str = "_archives",
        max_archives=10,
    ):
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

        existing_archives = [path for path in archive_dir.iterdir() if path.is_dir()]
        if len(existing_archives) >= max_archives:
            sorted_archives = sorted(existing_archives)
            num_to_delete = max(
                0, len(existing_archives) - max_archives + 1
            )  # +1 because we're about to archive the curr dir too.

            # We naively assume all items in the sorted archives dir are archives that have the same format as each other,
            # thus doing a naive sort will sort the archives by age (epoch timestamp).
            archives_to_delete = sorted_archives[:num_to_delete]
            for archive in archives_to_delete:
                logger.info(f">> Deleting old archive! '{archive}'")
                shutil.rmtree(archive)

        logger.info(f">> Archiving directory '{dir_to_archive}'")
        new_archive_name = f"{dir_to_archive.name}-{int(time.time())}"
        archive_destination = archive_dir / new_archive_name

        logger.info(
            f">> Archiving directory '{dir_to_archive}' -> '{archive_destination}'"
        )
        dir_to_archive.rename(archive_destination)

    def restore_minecraft(
        self, env: Env, world_group: str, target_id: str, worlds: List[str]
    ):
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

        world_files_dir = server_paths.get_data_dir_path(
            env.name, world_group, DataDirType.WORLD_FILES
        )

        self.archive_directory(
            world_files_dir,
        )

        cmd = f"restore {target_id} --target /"
        for world in worlds:
            cmd += f" --iinclude {BACKUP_CONTENT_ROOT}/{world}"

        out = self.call_restic(
            cmd,
            {
                "volumes": {
                    str(world_files_dir): {
                        "bind": BACKUP_CONTENT_ROOT,
                        "mode": "rw",
                    },
                }
            },
        )

        logger.info(out)

        return out
