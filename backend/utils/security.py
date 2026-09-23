import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from config.settings import settings

# PBKDF2-HMAC (stdlib) : hachage salé du mot de passe, sans dependance externe.
_ALGORITHME = "sha256"
_ITERATIONS = 200_000
_SEL_OCTETS = 16

ACCESS_TOKEN_TTL = timedelta(minutes=15)
REFRESH_TOKEN_TTL = timedelta(days=180)

_JWT_ALGORITHME = "HS256"
_TYPE_JETON_ACCES = "access"
_REFRESH_TOKEN_OCTETS = 48


class InvalidAccessTokenError(Exception):
    """Jeton d'acces expire, falsifie, malforme ou d'un autre type."""


def hash_password(mot_de_passe: str) -> str:
    sel = secrets.token_bytes(_SEL_OCTETS)
    derive = hashlib.pbkdf2_hmac(
        _ALGORITHME, mot_de_passe.encode("utf-8"), sel, _ITERATIONS
    )
    return f"pbkdf2_{_ALGORITHME}${_ITERATIONS}${sel.hex()}${derive.hex()}"


def verify_password(mot_de_passe: str, stocke: str) -> bool:
    try:
        algo_tag, iterations_brut, sel_hex, hash_hex = stocke.split("$")
        algorithme = algo_tag.split("_", 1)[1]
        iterations = int(iterations_brut)
        sel = bytes.fromhex(sel_hex)
        attendu = bytes.fromhex(hash_hex)
    except (ValueError, IndexError):
        return False

    derive = hashlib.pbkdf2_hmac(
        algorithme, mot_de_passe.encode("utf-8"), sel, iterations
    )
    return hmac.compare_digest(derive, attendu)


def _cle_de_signature() -> str:
    cle = settings.JWT_SECRET_KEY
    if not cle:
        raise RuntimeError("JWT_SECRET_KEY n'est pas configurée.")
    return cle


def create_access_token(user_id: UUID, now: datetime | None = None) -> str:
    emission = now or datetime.now(UTC)
    revendications = {
        "sub": str(user_id),
        "type": _TYPE_JETON_ACCES,
        "iat": emission,
        "exp": emission + ACCESS_TOKEN_TTL,
    }
    return jwt.encode(
        revendications, _cle_de_signature(), algorithm=_JWT_ALGORITHME
    )


def decode_access_token(token: str) -> UUID:
    try:
        revendications = jwt.decode(
            token,
            _cle_de_signature(),
            algorithms=[_JWT_ALGORITHME],
            options={"require": ["exp", "iat", "sub"]},
        )
        user_id = UUID(revendications["sub"])
    except (jwt.PyJWTError, ValueError) as erreur:
        raise InvalidAccessTokenError() from erreur

    if revendications.get("type") != _TYPE_JETON_ACCES:
        raise InvalidAccessTokenError()
    return user_id


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(_REFRESH_TOKEN_OCTETS)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
