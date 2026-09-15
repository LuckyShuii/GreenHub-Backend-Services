from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    # L'e-mail sert de login : unique et indexe.
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    pseudonyme: Mapped[str] = mapped_column(String(50), nullable=False)
    localisation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mot_de_passe_hache: Mapped[str] = mapped_column(String(255), nullable=False)
    date_creation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
