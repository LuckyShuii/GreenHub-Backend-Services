from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from database.deps import get_db
from models.user_model import User
from routers.dependencies import get_current_user
from schemas.auth_schema import (
    LoginRequest,
    RefreshSessionRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from schemas.user_schema import UserCreate, UserRead
from services.auth_service import (
    AuthService,
    EmailAlreadyUsedError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UsernameAlreadyUsedError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_EN_TETE_BEARER = {"WWW-Authenticate": "Bearer"}


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    service = AuthService(db)
    try:
        return service.register(payload)
    except EmailAlreadyUsedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette adresse e-mail est déjà utilisée.",
        )
    except UsernameAlreadyUsedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce pseudonyme est déjà utilisé.",
        )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    response.headers["Cache-Control"] = "no-store"
    service = AuthService(db)
    try:
        return service.login(payload)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
            headers=_EN_TETE_BEARER,
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshSessionRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    response.headers["Cache-Control"] = "no-store"
    service = AuthService(db)
    try:
        return service.refresh(payload.refresh_token, payload.device_info)
    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée. Veuillez vous reconnecter.",
            headers=_EN_TETE_BEARER,
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> None:
    AuthService(db).logout(payload.refresh_token)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return current_user
