from dataclasses import dataclass
from typing import List


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
