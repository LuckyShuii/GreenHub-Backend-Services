"""Tests HTTP des opérations authentifiées du profil."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from database.deps import get_db
from main import app
from models.user_model import User
from routers import auth_router as auth_router_module
from routers import dependencies as dependencies_module
from services.auth_service import EmailAlreadyUsedError, UsernameAlreadyUsedError
from utils.security import create_access_token

pytestmark = pytest.mark.unit

URL = "/api/auth/me"
USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture(autouse=True)
def sans_base_de_donnees():
    app.dependency_overrides[get_db] = lambda: None
    yield
    app.dependency_overrides.clear()


def _utilisateur() -> User:
    return User(
        id=USER_ID,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        username="ada",
        date_of_birth=None,
        postal_code="75000",
        password_hash="pbkdf2_sha256$200000$aa$bb",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _authentifier(
    monkeypatch: pytest.MonkeyPatch, utilisateur: User
) -> dict[str, str]:
    class FauxUserRepository:
        def __init__(self, db):
            self.db = db

        def get(self, user_id: UUID) -> User | None:
            return utilisateur if user_id == utilisateur.id else None

    monkeypatch.setattr(
        dependencies_module, "UserRepository", FauxUserRepository
    )
    return {
        "Authorization": f"Bearer {create_access_token(utilisateur.id)}"
    }


def test_patch_me_met_a_jour_le_profil_sans_exposer_le_hash(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    utilisateur = _utilisateur()
    headers = _authentifier(monkeypatch, utilisateur)

    class FauxAuthService:
        def __init__(self, db):
            self.db = db

        def update_profile(self, current_user: User, payload):
            current_user.first_name = payload.first_name
            current_user.username = payload.username
            current_user.postal_code = payload.postal_code
            return current_user

    monkeypatch.setattr(auth_router_module, "AuthService", FauxAuthService)

    response = client.patch(
        URL,
        headers=headers,
        json={
            "first_name": "Grace",
            "pseudonyme": "grace",
            "postal_code": "69000",
        },
    )

    assert response.status_code == 200
    assert response.json()["prenom"] == "Grace"
    assert response.json()["pseudonyme"] == "grace"
    assert response.json()["code_postal"] == "69000"
    assert "password_hash" not in response.json()


def test_patch_me_refuse_un_code_postal_invalide(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    headers = _authentifier(monkeypatch, _utilisateur())

    response = client.patch(
        URL,
        headers=headers,
        json={"postal_code": "7500"},
    )

    assert response.status_code == 422


def test_patch_me_renvoie_409_si_email_deja_utilise(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    headers = _authentifier(monkeypatch, _utilisateur())

    class FauxAuthService:
        def __init__(self, db):
            self.db = db

        def update_profile(self, current_user: User, payload):
            raise EmailAlreadyUsedError()

    monkeypatch.setattr(auth_router_module, "AuthService", FauxAuthService)

    response = client.patch(
        URL, headers=headers, json={"email": "taken@example.com"}
    )

    assert response.status_code == 409


def test_patch_me_renvoie_409_si_pseudonyme_deja_utilise(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    headers = _authentifier(monkeypatch, _utilisateur())

    class FauxAuthService:
        def __init__(self, db):
            self.db = db

        def update_profile(self, current_user: User, payload):
            raise UsernameAlreadyUsedError()

    monkeypatch.setattr(auth_router_module, "AuthService", FauxAuthService)

    response = client.patch(URL, headers=headers, json={"username": "taken"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Ce pseudonyme est déjà utilisé."


@pytest.mark.parametrize("username", [None, "", "   ", "a" * 51])
def test_patch_me_refuse_un_pseudonyme_invalide(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, username: str | None
):
    headers = _authentifier(monkeypatch, _utilisateur())

    response = client.patch(URL, headers=headers, json={"username": username})

    assert response.status_code == 422


def test_changement_mot_de_passe_enregistre_le_nouveau_mot_de_passe(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    headers = _authentifier(monkeypatch, _utilisateur())

    class FauxAuthService:
        def __init__(self, db):
            self.db = db

        def change_password(self, current_user: User, payload):
            current_user.password_hash = payload.new_password

    monkeypatch.setattr(auth_router_module, "AuthService", FauxAuthService)

    response = client.post(
        f"{URL}/password",
        headers=headers,
        json={"new_password": "NouveauMotDePasse1!"},
    )

    assert response.status_code == 204


def test_delete_me_supprime_le_compte_et_renvoie_204(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    utilisateur = _utilisateur()
    headers = _authentifier(monkeypatch, utilisateur)
    deleted: list[User] = []

    class FauxAuthService:
        def __init__(self, db):
            self.db = db

        def delete_account(self, current_user: User) -> None:
            deleted.append(current_user)

    monkeypatch.setattr(auth_router_module, "AuthService", FauxAuthService)

    response = client.delete(URL, headers=headers)

    assert response.status_code == 204
    assert response.content == b""
    assert deleted == [utilisateur]
