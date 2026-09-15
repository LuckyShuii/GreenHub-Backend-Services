"""Fixtures des tests d'integration : vraie base PostgreSQL + PostGIS.

Cible de la base de test, par ordre de priorite :

1. `TEST_DATABASE_URL` (utilise par la CI) ;
2. les variables `DB_*` de l'environnement (conteneur backend) ;
3. le `.env` a la racine du depot, mais sur la base `greener_test`.

Le schema est cree en jouant les migrations Alembic : une migration
oubliee fait echouer la suite, ce qu'un `create_all()` masquerait.

Chaque test s'execute dans une transaction annulee a la fin (les
`commit()` des repositories deviennent des SAVEPOINT), donc la base reste
vide entre deux tests sans avoir a la recreer.
"""

import os
import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from database.deps import get_db
from main import app

# backend/ : contient alembic.ini et migrations/
RACINE_BACKEND = Path(__file__).resolve().parents[2]
RACINE_DEPOT = RACINE_BACKEND.parent

BASE_DE_TEST_PAR_DEFAUT = "greener_test"
NOM_DE_BASE_VALIDE = re.compile(r"^[A-Za-z0-9_]+$")


def _lire_variable(cle: str, defaut: str | None = None) -> str | None:
    """Variable DB_*, depuis l'environnement puis le .env de la racine.

    On ne passe volontairement pas par `config.settings` : celui-ci
    charge `.env` *relativement au repertoire courant*, donc lance depuis
    `backend/` il ne voit pas le `.env` de la racine du depot. Les tests
    d'integration seraient alors ignores en silence alors qu'une base
    tourne -- un faux vert.
    """
    depuis_fichier = dotenv_values(RACINE_DEPOT / ".env")
    return os.environ.get(cle) or depuis_fichier.get(cle) or defaut


def _url_base_de_test() -> URL:
    brut = os.getenv("TEST_DATABASE_URL")
    if brut:
        return make_url(brut)

    return URL.create(
        drivername="postgresql+psycopg2",
        username=_lire_variable("DB_USER"),
        password=_lire_variable("DB_PASSWORD"),
        host=_lire_variable("DB_HOST", "localhost"),
        port=int(_lire_variable("DB_PORT", "5432")),
        database=BASE_DE_TEST_PAR_DEFAUT,
    )


def _verifier_cible(url: URL) -> None:
    """Garde-fou : refuse de migrer autre chose qu'une base de test.

    Sans cela, un `TEST_DATABASE_URL` mal copie ferait tourner la suite
    sur la base de developpement, dont les donnees seraient alterees.
    """
    nom = url.database or ""
    if not NOM_DE_BASE_VALIDE.match(nom):
        pytest.fail(f"Nom de base de test invalide : {nom!r}")
    if not nom.endswith("_test"):
        pytest.fail(
            "La base de test doit avoir un nom suffixe par '_test' "
            f"(recu : {nom!r}). Corrigez TEST_DATABASE_URL."
        )


def _abandonner(url: URL, erreur: Exception) -> None:
    """Ignore les tests en local, echoue en CI.

    En local, tout le monde n'a pas forcement de PostgreSQL lance ; en
    CI le service est garanti, donc une base injoignable est un bug.
    """
    if os.getenv("CI"):
        pytest.fail(
            f"Base de test injoignable ({url.render_as_string()}) : "
            f"{erreur}"
        )

    if not url.username:
        indice = (
            "aucun DB_USER trouve : copiez `.env.example` vers `.env` a "
            "la racine du depot et renseignez DB_USER / DB_PASSWORD."
        )
    else:
        indice = "demarrez-la avec `docker compose up -d postgres`."

    pytest.skip(
        f"Tests d'integration ignores -- base injoignable "
        f"({url.render_as_string()}) ; {indice}"
    )


def _creer_base_si_absente(url: URL) -> None:
    """CREATE DATABASE ne peut pas tourner dans une transaction."""
    moteur = create_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        with moteur.connect() as connexion:
            existe = connexion.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :nom"),
                {"nom": url.database},
            ).scalar()
            if not existe:
                connexion.execute(
                    text(f'CREATE DATABASE "{url.database}"')
                )
    finally:
        moteur.dispose()


def _appliquer_migrations(url: URL) -> None:
    config = Config(str(RACINE_BACKEND / "alembic.ini"))
    config.set_main_option(
        "script_location", str(RACINE_BACKEND / "migrations")
    )
    # Lu par migrations/env.py, qui prime sur l'URL de `database.session`.
    config.attributes["sqlalchemy_url"] = url.render_as_string(
        hide_password=False
    )
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def moteur() -> Iterator[Engine]:
    """Engine sur la base de test, migree une seule fois par session."""
    url = _url_base_de_test()
    _verifier_cible(url)

    try:
        _creer_base_si_absente(url)
        moteur_test = create_engine(url, pool_pre_ping=True)
        with moteur_test.begin() as connexion:
            # PostGIS est installe par database/init/ dans le compose ;
            # en CI le service demarre sans ce script, d'ou la creation
            # explicite ici.
            connexion.execute(
                text("CREATE EXTENSION IF NOT EXISTS postgis")
            )
        _appliquer_migrations(url)
    except SQLAlchemyError as erreur:
        _abandonner(url, erreur)

    yield moteur_test

    moteur_test.dispose()


@pytest.fixture
def db_session(moteur: Engine) -> Iterator[Session]:
    """Session isolee : tout ce que le test ecrit est annule a la fin.

    `join_transaction_mode="create_savepoint"` fait que les `commit()`
    des repositories liberent un SAVEPOINT au lieu de valider la
    transaction externe, qu'on annule ensuite.
    """
    connexion = moteur.connect()
    transaction = connexion.begin()
    fabrique = sessionmaker(
        bind=connexion,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )
    session = fabrique()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connexion.close()


@pytest.fixture
def client_api(db_session: Session) -> Iterator[TestClient]:
    """Client HTTP dont les routes ecrivent dans la session du test."""
    app.dependency_overrides[get_db] = lambda: db_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
