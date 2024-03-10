import json
import docker
from docker.models.containers import Container

from dataclasses import dataclass
from typing import List, Dict
from pprint import pformat

from src.api.lib.helpers import container_name_to_container
from src.common.logger_setup import logger
from src.common.environment import Env
from src.common.constants import YC_ENV_LABEL, YC_CONTAINER_NAME_LABEL, HOST_REPO_ROOT_PATH

class InvalidContainerException(Exception):
    pass
class ContainerMissingEnvLabelException(InvalidContainerException):
    pass
class ContainerMissingNameLabelException(InvalidContainerException):
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
    time: str # datetime?
    tree: str
    username: str


class BackupManagement:
    def __init__(self):
        self.docker_client = docker.from_env()

    def container_name_to_container(self, container_name):
        return container_name_to_container(self.client, container_name)

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
                "/media/backups-primary/restic": {
                    "bind": "/backups",
                    "mode": "rw",
                },
                f"{HOST_REPO_ROOT_PATH}/secrets/restic.password": {
                    "bind": "/restic.password",
                    "mode": "ro",
                }
            },
        )

        if isinstance(response_as_json, bytes):
            response_as_json = response_as_json.decode("utf-8")

        backups = json.loads(response_as_json)

        logger.info("RESPONSE FROM RESTIC SNAPSHOTS")
        logger.info(pformat(backups))

        return list(filter(
            lambda backup: BackupManagement.contains_tags(backup, tags),
            backups
        ))
