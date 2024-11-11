from typing import List, Optional
from pydantic import BaseModel # type: ignore


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

class Backup(BaseModel):
    excludes: List[str]
    gid: int
    hostname: str
    id: str
    paths: List[str]
    program_version: str
    short_id: str
    tags: List[str]
    time: str  # datetime?
    tree: str
    uid: int
    username: str

    parent: Optional[str] = None
