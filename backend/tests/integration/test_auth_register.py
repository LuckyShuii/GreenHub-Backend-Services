"""Parcours complet d'inscription : HTTP -> service -> PostgreSQL.

Contrairement aux tests unitaires du router, rien n'est simule ici :
c'est le seul endroit qui prouve que la chaine entiere fonctionne.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from repositories.user_repository import UserRepository
from utils.security import verify_password

pytestmark = pytest.mark.integration

URL = "/api/auth/register"


def test_inscription_cree_l_utilisateur_en_base(
    client_api: TestClient,
    db_session: Session,
    payload_inscription: dict,
):
    reponse = client_api.post(URL, json=payload_inscription)

    assert reponse.status_code == 201
    enregistre = UserRepository(db_session).get_by_email(
        "ada@example.com"
    )
    assert enregistre is not None
    assert enregistre.id == reponse.json()["id"]


def test_inscription_stocke_le_mot_de_passe_hache(
    client_api: TestClient,
    db_session: Session,
    payload_inscription: dict,
):
    """Aucun mot de passe en clair ne doit atteindre la base."""
    client_api.post(URL, json=payload_inscription)

    enregistre = UserRepository(db_session).get_by_email(
        "ada@example.com"
    )
    assert enregistre.mot_de_passe_hache != "MotDePasse1!"
    assert verify_password(
        "MotDePasse1!", enregistre.mot_de_passe_hache
    )


def test_la_reponse_n_expose_pas_le_mot_de_passe(
    client_api: TestClient, payload_inscription: dict
):
    corps = client_api.post(URL, json=payload_inscription).json()

    assert "mot_de_passe" not in corps
    assert "mot_de_passe_hache" not in corps


def test_inscription_normalise_l_email_avant_insertion(
    client_api: TestClient,
    db_session: Session,
    payload_inscription: dict,
):
    payload_inscription["email"] = "ADA@Example.COM"

    reponse = client_api.post(URL, json=payload_inscription)

    assert reponse.json()["email"] == "ada@example.com"
    assert (
        UserRepository(db_session).get_by_email("ada@example.com")
        is not None
    )


def test_email_deja_inscrit_renvoie_409(
    client_api: TestClient, payload_inscription: dict
):
    client_api.post(URL, json=payload_inscription)

    reponse = client_api.post(URL, json=payload_inscription)

    assert reponse.status_code == 409


def test_le_doublon_ne_cree_pas_de_second_utilisateur(
    client_api: TestClient,
    db_session: Session,
    payload_inscription: dict,
):
    client_api.post(URL, json=payload_inscription)
    client_api.post(URL, json=payload_inscription)

    assert len(UserRepository(db_session).get_all()) == 1


def test_deux_utilisateurs_distincts_sont_acceptes(
    client_api: TestClient,
    db_session: Session,
    payload_inscription: dict,
):
    client_api.post(URL, json=payload_inscription)
    client_api.post(
        URL, json={**payload_inscription, "email": "grace@example.com"}
    )

    assert len(UserRepository(db_session).get_all()) == 2


def test_payload_invalide_n_ecrit_rien_en_base(
    client_api: TestClient,
    db_session: Session,
    payload_inscription: dict,
):
    payload_inscription["mot_de_passe"] = "faible"

    reponse = client_api.post(URL, json=payload_inscription)

    assert reponse.status_code == 422
    assert UserRepository(db_session).get_all() == []
