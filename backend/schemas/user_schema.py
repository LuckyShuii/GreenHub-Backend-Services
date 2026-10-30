from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(max_length=255)
    username: str = Field(min_length=1, max_length=50)
    date_of_birth: date | None = None
    postal_code: Annotated[
        str | None,
        Field(
            min_length=5,
            max_length=5,
            pattern=r"^\d{5}$",
        ),
    ] = None
    mot_de_passe: str = Field(min_length=12, max_length=128)

    @model_validator(mode="before")
    @classmethod
    def _normaliser_noms_de_champs(cls, values: object) -> object:
        if not isinstance(values, dict):
            return values
        normalized = values.copy()
        aliases = {
            "prenom": "first_name",
            "nom": "last_name",
            "pseudonyme": "username",
            "code_postal": "postal_code",
        }
        for alias, field_name in aliases.items():
            if alias in normalized:
                normalized.setdefault(field_name, normalized[alias])
                del normalized[alias]
        return normalized

    @field_validator("mot_de_passe")
    @classmethod
    def _valider_mot_de_passe(cls, value: str) -> str:
        _validate_password(value)
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


class UserUpdate(BaseModel):
    first_name: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    last_name: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    username: Annotated[str | None, Field(min_length=1, max_length=50)] = None
    email: EmailStr | None = None
    postal_code: Annotated[
        str | None,
        Field(
            min_length=5,
            max_length=5,
            pattern=r"^\d{5}$",
        ),
    ] = None

    @model_validator(mode="before")
    @classmethod
    def _normaliser_pseudonyme(cls, values: object) -> object:
        if not isinstance(values, dict):
            return values
        normalized = values.copy()
        if "pseudonyme" in normalized:
            normalized.setdefault("username", normalized.pop("pseudonyme"))
        return normalized

    @field_validator("username", mode="before")
    @classmethod
    def _nettoyer_pseudonyme(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("first_name", "last_name")
    @classmethod
    def _nettoyer_nom(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Ce champ est requis.")
        return cleaned

    @field_validator("email")
    @classmethod
    def _normaliser_email_modifie(cls, value: EmailStr | None) -> EmailStr | None:
        return value.lower().strip() if value is not None else None

    @field_validator("postal_code", mode="before")
    @classmethod
    def _nettoyer_code_postal(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @model_validator(mode="after")
    def _refuser_corps_vide_ou_valeurs_nulles(self) -> "UserUpdate":
        if not self.model_fields_set:
            raise ValueError("Au moins un champ doit être modifié.")
        for field_name in ("first_name", "last_name", "email", "username"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError("Ce champ ne peut pas être vide.")
        return self


class PasswordChange(BaseModel):
    new_password: str = Field(
        min_length=12,
        max_length=128,
    )

    @field_validator("new_password")
    @classmethod
    def _valider_nouveau_mot_de_passe(cls, value: str) -> str:
        _validate_password(value)
        return value


def _validate_password(value: str) -> None:
    if not any(character.isupper() for character in value):
        raise ValueError("Le mot de passe doit contenir une majuscule.")
    if not any(character.islower() for character in value):
        raise ValueError("Le mot de passe doit contenir une minuscule.")
    if not any(character.isdigit() for character in value):
        raise ValueError("Le mot de passe doit contenir un chiffre.")
    if not any(not character.isalnum() for character in value):
        raise ValueError("Le mot de passe doit contenir un caractère spécial.")
