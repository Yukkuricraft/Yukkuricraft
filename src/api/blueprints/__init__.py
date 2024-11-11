from typing import List
from flask_openapi3 import Tag  # type: ignore
from pydantic import BaseModel, Field  # type: ignore

from src.api.lib import Backup, LegacyActiveContainer, LegacyDefinedContainer
from src.common.environment import Env, EnvModel

auth_tag = Tag(name="Authorization", description="Authorization endpoints")
backups_tag = Tag(name="Backups", description="Backup endpoints")
environment_tag = Tag(
    name="Environments", description="Environment management endpoints"
)
files_tag = Tag(name="Files", description="File management endpoints")
server_tag = Tag(name="Server", description="Server management endpoints")
sockets_tag = Tag(name="Sockets", description="Sockets endpoints")


class UnauthorizedResponse(BaseModel):
    message: str = Field(description="A message")


class EnvRequestPath(BaseModel):
    env_str: str = Field(description="Environment id string")


class ContainerNameRequestPath(BaseModel):
    container_name: str = Field(description="Container name string")


# -----------
# Auth Models
# -----------


class MeResponse(BaseModel):
    sub: str = Field(description="Subject ID")
    email: str = Field(description="Email of the subject")


class LoginRequestBody(BaseModel):
    id_token: str = Field(description="id_token is provided by the Google OAuth2 flow.")


class LoginResponse(BaseModel):
    access_token: str = Field(description="YC generated access token")


# -----------
# Backups Models
# -----------


class ListBackupsRequestBody(BaseModel):
    env_str: str = Field(description="Environment id string")
    target_tags: List[str] = Field(description="Restic target tags to filter for")


class ListBackupsResponse(BaseModel):
    backups: List[Backup] = Field(description="List of backups found")


class CreateBackupRequestBody(BaseModel):
    target_env: str = Field(description="Environment to create backup for")
    target_world_group: str = Field(
        description="World group name to backup within the target_env"
    )


class CreateBackupResponse(BaseModel):
    success: bool = Field(description="Whether the backup succeeded or not")
    output: str = Field(description="Stdout from the backup container run")


class RestoreBackupRequestBody(BaseModel):
    target_hostname: str = Field(description="Hostname of container to restore")
    target_snapshot_id: str = Field(
        description="The restic snapshot ID for the backup to restore"
    )


class RestoreBackupResponse(BaseModel):
    success: bool = Field(description="Whether the backup succeeded or not")
    output: str = Field(description="Stdout from the backup container run")


# ------------------
# Environment Models
# ------------------


class CreateEnvironmentRequestBody(BaseModel):
    PROXY_PORT: int = Field(description="Proxy port")
    ENV_ALIAS: str = Field(description="Env alias")
    DESCRIPTION: str = Field(description="Env description")
    SERVER_TYPE: str = Field(description="Server type of environment")
    ENABLE_ENV_PROTECTION: str = Field(
        description="Whether env protection is enabled or not", default=False
    )


class CreateEnvironmentResponse(BaseModel):
    created_env: EnvModel = Field(description="Environment that was created")


class DeleteEnvironmentResponse(BaseModel):
    success: bool = Field(description="Whether the deletion was successful or not")
    env: EnvModel = Field(description="The env we attempted to delete")


class GenerateConfigsResponse(BaseModel):
    env: EnvModel = Field(description="The env we generated configs for")


class ListEnvironmentsResponse(BaseModel):
    envs: List[EnvModel] = Field(description="List of all defined envs")


# -----------------------
# Server/Container Models
# -----------------------


class ListDefinedContainersResponse(BaseModel):
    defined_containers: List[LegacyDefinedContainer] = Field(
        description="List of defined containers"
    )


class ListActiveContainersResponse(BaseModel):
    active_containers: List[LegacyActiveContainer] = Field(
        description="List of currently running containers"
    )
