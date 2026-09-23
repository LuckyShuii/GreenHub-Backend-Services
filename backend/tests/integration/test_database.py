"""Verifie que la base de test est bien celle attendue par l'app.

Si ces tests echouent, ceux qui suivent sont ininterpretables : ils
valident le socle (PostGIS active, schema migre) avant la logique.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from models.user_model import User

pytestmark = pytest.mark.integration


def test_la_base_repond(db_session: Session):
    assert db_session.execute(text("SELECT 1")).scalar() == 1


def test_postgis_est_active(db_session: Session):
    """La strategie V1 s'appuie sur PostGIS pour la geolocalisation."""
    version = db_session.execute(text("SELECT postgis_version()")).scalar()

    assert version


def test_la_table_users_existe_avec_ses_colonnes(moteur: Engine):
    colonnes = {
        colonne["name"]
        for colonne in inspect(moteur).get_columns("users")
    }

    assert colonnes == {
        "id",
        "email",
        "first_name",
        "last_name",
        "username",
        "date_of_birth",
        "postal_code",
        "password_hash",
        "created_at",
    }


def test_l_email_est_indexe(moteur: Engine):
    """L'e-mail sert de login : la recherche doit passer par un index."""
    index = {i["name"] for i in inspect(moteur).get_indexes("users")}

    assert "idx_users_email" in index


def test_le_modele_ne_derive_pas_des_migrations(moteur: Engine):
    """Colonnes declarees en SQLAlchemy == colonnes reellement en base.

    Detecte l'oubli classique : un champ ajoute au modele sans migration.
    """
    attendues = {colonne.name for colonne in User.__table__.columns}
    reelles = {
        colonne["name"]
        for colonne in inspect(moteur).get_columns("users")
    }

    assert attendues == reelles


def test_health_db_interroge_la_vraie_base(client_api: TestClient):
    """La sonde de readiness passe par une vraie connexion, pas un mock."""
    reponse = client_api.get("/health/db")

    assert reponse.status_code == 200
    assert reponse.json() == {"status": "ok", "database": "reachable"}
