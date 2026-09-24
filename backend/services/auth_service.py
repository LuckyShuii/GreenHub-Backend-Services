import secrets
from datetime import UTC, datetime
from functools import cache
from re import fullmatch
from uuid import UUID

from sqlalchemy.orm import Session

from models.session_model import UserSession
from models.user_model import User
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from schemas.auth_schema import LoginRequest, TokenResponse
from schemas.user_schema import UserCreate
from utils.security import (
    ACCESS_TOKEN_TTL,
    REFRESH_TOKEN_TTL,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


class EmailAlreadyUsedError(Exception):
    """L'inscription cible une adresse e-mail deja enregistree."""


class UsernameAlreadyUsedError(Exception):
    """L'inscription cible un pseudonyme deja enregistre."""


class InvalidCredentialsError(Exception):
    """E-mail inconnu ou mot de passe faux, volontairement indistincts."""


class InvalidRefreshTokenError(Exception):
    """Refresh token inconnu, expire ou deja revoque."""


@cache
def _empreinte_factice() -> str:
    return hash_password(secrets.token_urlsafe(16))


class AuthService:
    def __init__(self, db: Session):
        self._users = UserRepository(db)
        self._sessions = SessionRepository(db)

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

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self._users.get_by_email(payload.email)
        if user is None:
            # Meme cout PBKDF2 qu'un vrai compte : le temps de reponse ne revele pas l'e-mail.
            verify_password(payload.mot_de_passe, _empreinte_factice())
            raise InvalidCredentialsError()
        if not verify_password(payload.mot_de_passe, user.password_hash):
            raise InvalidCredentialsError()

        return self._ouvrir_session(user.id, payload.device_info)

    def refresh(
        self, refresh_token: str, device_info: str
    ) -> TokenResponse:
        session_utilisateur = self._sessions.get_by_refresh_token_hash(
            hash_refresh_token(refresh_token)
        )
        if session_utilisateur is None:
            raise InvalidRefreshTokenError()
        if session_utilisateur.revoked:
            raise InvalidRefreshTokenError()
        if session_utilisateur.expires_at <= datetime.now(UTC):
            session_utilisateur.revoked = True
            self._sessions.update(session_utilisateur)
            raise InvalidRefreshTokenError()

        if device_info != session_utilisateur.device_info:
            raise InvalidRefreshTokenError()

        session_utilisateur.expires_at = datetime.now(UTC) + REFRESH_TOKEN_TTL
        self._sessions.update(session_utilisateur)

        return self._token_response(session_utilisateur.user_id, refresh_token)

    def logout(self, refresh_token: str) -> None:
        session_utilisateur = self._sessions.get_by_refresh_token_hash(
            hash_refresh_token(refresh_token)
        )
        if session_utilisateur is None or session_utilisateur.revoked:
            return

        session_utilisateur.revoked = True
        self._sessions.update(session_utilisateur)

    def _ouvrir_session(
        self,
        user_id: UUID,
        device_info: str,
    ) -> TokenResponse:
        refresh_token = generate_refresh_token()
        session_utilisateur = self._sessions.get_by_user_and_device(
            user_id, device_info
        )
        if session_utilisateur is None:
            self._sessions.create(
                UserSession(
                    user_id=user_id,
                    refresh_token_hash=hash_refresh_token(refresh_token),
                    device_info=device_info,
                    expires_at=datetime.now(UTC) + REFRESH_TOKEN_TTL,
                )
            )
        else:
            session_utilisateur.refresh_token_hash = hash_refresh_token(refresh_token)
            session_utilisateur.device_info = device_info
            session_utilisateur.expires_at = datetime.now(UTC) + REFRESH_TOKEN_TTL
            session_utilisateur.revoked = False
            self._sessions.update(session_utilisateur)

        return self._token_response(
            user_id,
            refresh_token,
        )

    def _token_response(self, user_id: UUID, refresh_token: str) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=refresh_token,
            expires_in=int(ACCESS_TOKEN_TTL.total_seconds()),
        )
