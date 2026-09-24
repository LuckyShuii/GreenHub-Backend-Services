from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database.deps import get_db
from models.user_model import User
from repositories.user_repository import UserRepository
from utils.security import InvalidAccessTokenError, decode_access_token

# auto_error=False : sans en-tete, HTTPBearer renverrait 403 au lieu du 401 attendu.
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    non_authentifie = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expirée ou invalide.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise non_authentifie

    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidAccessTokenError:
        raise non_authentifie from None

    user = UserRepository(db).get(user_id)
    if user is None:
        raise non_authentifie
    return user
