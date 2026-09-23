from datetime import date, datetime
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class UserCreate(BaseModel):
    first_name: str = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("first_name", "prenom"),
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("last_name", "nom"),
    )
    email: EmailStr = Field(max_length=255)
    username: str = Field(
        min_length=1,
        max_length=50,
        validation_alias=AliasChoices("username", "pseudonyme"),
    )
    date_of_birth: date | None = None
    postal_code: str | None = Field(
        default=None,
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
        validation_alias=AliasChoices("postal_code", "code_postal"),
    )
    localisation: str | None = Field(default=None, max_length=255)
    mot_de_passe: str = Field(min_length=12, max_length=128)

    @field_validator("mot_de_passe")
    @classmethod
    def _valider_mot_de_passe(cls, value: str) -> str:
        if not any(character.isupper() for character in value):
            raise ValueError("Le mot de passe doit contenir une majuscule.")
        if not any(character.islower() for character in value):
            raise ValueError("Le mot de passe doit contenir une minuscule.")
        if not any(character.isdigit() for character in value):
            raise ValueError("Le mot de passe doit contenir un chiffre.")
        if not any(not character.isalnum() for character in value):
            raise ValueError(
                "Le mot de passe doit contenir un caractère spécial."
            )
        return value

    @field_validator("first_name", "last_name", "username")
    @classmethod
    def _nettoyer(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def _normaliser_email(cls, value: str) -> str:
        return value.strip().lower()


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str = Field(serialization_alias="prenom")
    last_name: str = Field(serialization_alias="nom")
    email: EmailStr
    username: str = Field(serialization_alias="pseudonyme")
    date_of_birth: date | None = Field(serialization_alias="date_naissance")
    postal_code: str | None = Field(serialization_alias="code_postal")
    created_at: datetime = Field(serialization_alias="date_creation")

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)
