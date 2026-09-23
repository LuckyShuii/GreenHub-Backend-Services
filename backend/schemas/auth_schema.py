from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    # Ni EmailStr ni politique de mot de passe : toute saisie erronee doit finir en 401, pas en 422.
    email: str = Field(min_length=1, max_length=255)
    mot_de_passe: str = Field(min_length=1, max_length=128)
    device_info: str = Field(min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def _normaliser_email(cls, value: str) -> str:
        return value.strip().lower()


class RefreshSessionRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=255)
    device_info: str = Field(min_length=1, max_length=255)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
