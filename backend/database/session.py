# db/session.py
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from config.settings import settings

# Construction de l'URL à partir des composants individuels.
# DB_USER / DB_PASSWORD peuvent être None (SCRUM-114) : l'engine est quand
# même créé, mais aucune connexion réelle n'est tentée tant qu'aucune
# requête n'est exécutée (lazy connection de SQLAlchemy).
_database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)

engine = create_engine(_database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)