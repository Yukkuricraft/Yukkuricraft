from typing import Dict, List, Optional, Union
from pydantic import BaseModel  # type: ignore


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
    gid: int
    hostname: str
    id: str
    paths: List[str]
    program_version: str
    short_id: str
    time: str  # datetime?
    tree: str
    uid: int
    username: str

    tags: Optional[List[str]] = None # If no --tag arg supplied at backup time
    excludes: Optional[List[str]] = None # If no --exclude arg supplied at backup time
    parent: Optional[str] = None # If first backup


# See docker_management.convert_dockerpy_container_to_container_definition
class LegacyActiveContainer(BaseModel):
    Command: Union[List[str], str]
    ContainerName: str
    CreatedAt: str
    Hostname: str
    ID: str
    Image: str
    Labels: Dict[str, str]
    Mounts: List[str]
    Names: List[str]
    Networks: List[str]
    Ports: List[str]
    RunningFor: str
    State: str
    Status: str


# See docker_management.list_defined_containers
class LegacyDefinedContainer(BaseModel):
    image: str
    names: List[str]
    container_name: str
    hostname: str
    mounts: List[str]
    networks: List[str]
    ports: List[str]
    labels: Dict[str, str]
