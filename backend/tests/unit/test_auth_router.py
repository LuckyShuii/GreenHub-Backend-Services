"""Tests unitaires de la route POST /api/auth/register.

La couche service est remplacee par un double : ce fichier ne verifie que
le contrat HTTP (codes de statut, corps de reponse, validation d'entree).
La logique metier est couverte par `test_auth_service.py`, le parcours
reel par les tests d'integration.
"""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from database.deps import get_db
from main import app
from models.user_model import User
from routers import auth_router as auth_router_module
from services.auth_service import EmailAlreadyUsedError

pytestmark = pytest.mark.unit

URL = "/api/auth/register"


@pytest.fixture(autouse=True)
def sans_base_de_donnees():
    """Neutralise `get_db` : aucun test de ce fichier ne touche PostgreSQL."""
    app.dependency_overrides[get_db] = lambda: None
    yield
    app.dependency_overrides.clear()


def _utilisateur_enregistre(payload: dict) -> User:
    return User(
        id=1,
        prenom=payload["prenom"],
        nom=payload["nom"],
        email=payload["email"],
        pseudonyme=payload["pseudonyme"],
        localisation=payload.get("localisation"),
        mot_de_passe_hache="pbkdf2_sha256$200000$aa$bb",
        date_creation=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _brancher_service(
    monkeypatch: pytest.MonkeyPatch, register
) -> None:
    """Remplace AuthService par un double dont `register` est fourni."""

    class FauxAuthService:
        def __init__(self, db):
            self.db = db

        def register(self, payload):
            return register(payload)

    monkeypatch.setattr(
        auth_router_module, "AuthService", FauxAuthService
    )


def test_inscription_reussie_renvoie_201(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    payload_inscription: dict,
):
    _brancher_service(
        monkeypatch,
        lambda _: _utilisateur_enregistre(payload_inscription),
    )

    reponse = client.post(URL, json=payload_inscription)

    assert reponse.status_code == 201


def test_inscription_reussie_renvoie_l_utilisateur_sans_mot_de_passe(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    payload_inscription: dict,
):
    _brancher_service(
        monkeypatch,
        lambda _: _utilisateur_enregistre(payload_inscription),
    )

    corps = client.post(URL, json=payload_inscription).json()

    assert corps["id"] == 1
    assert corps["email"] == "ada@example.com"
    assert "mot_de_passe" not in corps
    assert "mot_de_passe_hache" not in corps


def test_le_service_recoit_le_payload_valide(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    payload_inscription: dict,
):
    recus = []

    def register(payload):
        recus.append(payload)
        return _utilisateur_enregistre(payload_inscription)

    _brancher_service(monkeypatch, register)

    client.post(URL, json=payload_inscription)

    assert len(recus) == 1
    assert recus[0].email == "ada@example.com"
    # Le router transmet le schema Pydantic, pas le JSON brut.
    assert recus[0].mot_de_passe == "MotDePasse1!"


def test_email_deja_utilise_renvoie_409(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    payload_inscription: dict,
):
    def register(_):
        raise EmailAlreadyUsedError()

    _brancher_service(monkeypatch, register)

    reponse = client.post(URL, json=payload_inscription)

    assert reponse.status_code == 409
    assert "deja utilisee" in reponse.json()["detail"]


def test_payload_invalide_renvoie_422_sans_appeler_le_service(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    payload_inscription: dict,
):
    """La validation Pydantic s'applique avant d'atteindre le service."""
    appels = []

    def register(payload):
        appels.append(payload)
        return _utilisateur_enregistre(payload_inscription)

    _brancher_service(monkeypatch, register)
    payload_inscription["mot_de_passe"] = "faible"

    reponse = client.post(URL, json=payload_inscription)

    assert reponse.status_code == 422
    assert appels == []


def test_corps_vide_renvoie_422(client: TestClient):
    assert client.post(URL, json={}).status_code == 422


def test_la_route_est_montee_sous_le_prefixe_api(
    client: TestClient, payload_inscription: dict
):
    """Garde-fou : /auth/register sans /api ne doit pas exister."""
    assert client.post(
        "/auth/register", json=payload_inscription
    ).status_code == 404
