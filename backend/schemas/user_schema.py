from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    prenom: str = Field(min_length=1, max_length=100)
    nom: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(max_length=255)
    pseudonyme: str = Field(min_length=1, max_length=50)
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

    @field_validator("prenom", "nom", "pseudonyme")
    @classmethod
    def _nettoyer(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def _normaliser_email(cls, value: str) -> str:
        return value.strip().lower()


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prenom: str
    nom: str
    email: EmailStr
    pseudonyme: str
    localisation: str | None
    date_creation: datetime
