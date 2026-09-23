from re import fullmatch

from sqlalchemy.orm import Session

from models.user_model import User
from repositories.user_repository import UserRepository
from schemas.user_schema import UserCreate
from utils.security import hash_password


class EmailAlreadyUsedError(Exception):
    """L'inscription cible une adresse e-mail deja enregistree."""


class UsernameAlreadyUsedError(Exception):
    """L'inscription cible un pseudonyme deja enregistre."""


class AuthService:
    def __init__(self, db: Session):
        self._users = UserRepository(db)

    def register(self, payload: UserCreate) -> User:
        if self._users.get_by_email(payload.email) is not None:
            raise EmailAlreadyUsedError()
        if self._users.get_by_username(payload.username) is not None:
            raise UsernameAlreadyUsedError()

        postal_code = payload.postal_code
        if postal_code is None and payload.localisation:
            if fullmatch(r"\d{5}", payload.localisation):
                postal_code = payload.localisation

        user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            username=payload.username,
            date_of_birth=payload.date_of_birth,
            postal_code=postal_code,
            password_hash=hash_password(payload.mot_de_passe),
        )
        return self._users.create(user)
