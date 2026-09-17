from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.deps import get_db
from schemas.user_schema import UserCreate, UserRead
from services.auth_service import (
    AuthService,
    EmailAlreadyUsedError,
    UsernameAlreadyUsedError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


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
