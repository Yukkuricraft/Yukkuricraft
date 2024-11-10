from flask_openapi3 import Tag # type: ignore
from pydantic import BaseModel, Field # type: ignore

auth_tag = Tag(name='Authorization', description="Authorization endpoints")
backups_tag = Tag(name='Backups', description="Backup endpoints")
environment_tag = Tag(name='Environments', description="Environment management endpoints")
files_tag = Tag(name='Files', description="File management endpoints")
server_tag = Tag(name='Server', description="Server management endpoints")
sockets_tag = Tag(name='Sockets', description="Sockets endpoints")

class UnauthorizedResponse(BaseModel):
    message: str = Field(description="A message")

class MeResponse(BaseModel):
    sub: str = Field(description="Subject ID")
    email: str = Field(description="Email of the subject")

class EnvRequestPath(BaseModel):
    env_str: str = Field(..., description="Environment id string")

class LoginRequestBody(BaseModel):
    id_token: str = Field(description="id_token is provided by the Google OAuth2 flow.")

class LoginResponseBody(BaseModel):
    access_token: str = Field(description="YC generated access token")