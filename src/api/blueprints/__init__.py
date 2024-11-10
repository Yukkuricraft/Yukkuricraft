from pydantic import BaseModel, Field # type: ignore


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