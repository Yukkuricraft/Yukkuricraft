from typing import List
from flask_openapi3 import Tag  # type: ignore
from pydantic import BaseModel, Field  # type: ignore

from src.api.lib import Backup, LegacyActiveContainer, LegacyDefinedContainer

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


# ------------------
# Environment Models
# ------------------


class ListDefinedContainersResponse(BaseModel):
    defined_containers: List[LegacyDefinedContainer] = Field(
        description="List of defined containers"
    )


class ListActiveContainersResponse(BaseModel):
    active_containers: List[LegacyActiveContainer] = Field(
        description="List of currently running containers"
    )


# -----------------------
# Server/Container Models
# -----------------------
