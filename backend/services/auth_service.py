from sqlalchemy.orm import Session

from models.user_model import User
from repositories.user_repository import UserRepository
from schemas.user_schema import UserCreate
from utils.security import hash_password


class EmailAlreadyUsedError(Exception):
    """L'inscription cible une adresse e-mail deja enregistree."""


class AuthService:
    def __init__(self, db: Session):
        self._users = UserRepository(db)

    def register(self, payload: UserCreate) -> User:
        if self._users.get_by_email(payload.email) is not None:
            raise EmailAlreadyUsedError()

        user = User(
            prenom=payload.prenom,
            nom=payload.nom,
            email=payload.email,
            pseudonyme=payload.pseudonyme,
            localisation=payload.localisation,
            mot_de_passe_hache=hash_password(payload.mot_de_passe),
        )
        return self._users.create(user)
