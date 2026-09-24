from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from models.session_model import UserSession
from repositories.base import BaseRepository


class SessionRepository(BaseRepository[UserSession]):
    def __init__(self, db: Session):
        super().__init__(UserSession, db)

    def get_by_refresh_token_hash(self, token_hash: str) -> UserSession | None:
        return (
            self.db.query(UserSession)
            .filter(UserSession.refresh_token_hash == token_hash)
            .first()
        )

    def get_by_user_and_device(
        self, user_id: UUID, device_info: str
    ) -> UserSession | None:
        return (
            self.db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.device_info == device_info,
            )
            .first()
        )

    def revoke_all_for_user(self, user_id: UUID) -> None:
        self.db.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked.is_(False),
            )
            .values(revoked=True)
        )
        self.db.commit()
