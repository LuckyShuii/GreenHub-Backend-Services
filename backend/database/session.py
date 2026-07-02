# db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import get_settings

settings = get_settings()

# echo=False en prod ; lazy connection, ne se connecte pas tant qu'aucune requête n'est faite
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)