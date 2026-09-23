"""Tests unitaires des routes de session : login, refresh, logout et me.

Comme pour l'inscription, la couche service est remplacee par un double :
seul le contrat HTTP est verifie ici (codes, en-tetes, corps).
"""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from database.deps import get_db
from main import app
from models.user_model import User
from routers import auth_router as auth_router_module
from routers import dependencies as dependencies_module
from schemas.auth_schema import TokenResponse
from services.auth_service import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from utils.security import create_access_token

pytestmark = pytest.mark.unit

URL_LOGIN = "/api/auth/login"
URL_REFRESH = "/api/auth/refresh"
URL_LOGOUT = "/api/auth/logout"
URL_ME = "/api/auth/me"

CORPS_LOGIN = {
    "email": "ada@example.com",
    "mot_de_passe": "MotDePasse1!",
    "device_info": "device-1",
}
IDENTIFIANT = UUID("00000000-0000-0000-0000-000000000001")
JETONS = TokenResponse(
    access_token="acces", refresh_token="rafraichissement", expires_in=900
)


@pytest.fixture(autouse=True)
def sans_base_de_donnees():
    """Neutralise `get_db` : aucun test de ce fichier ne touche PostgreSQL."""
    app.dependency_overrides[get_db] = lambda: None
    yield
    app.dependency_overrides.clear()


def _brancher_service(monkeypatch: pytest.MonkeyPatch, **methodes) -> None:
    """Remplace AuthService par un double exposant les methodes fournies."""

    class FauxAuthService:
        def __init__(self, db):
            self.db = db

    for nom, implementation in methodes.items():
        setattr(FauxAuthService, nom, staticmethod(implementation))

    monkeypatch.setattr(auth_router_module, "AuthService", FauxAuthService)


def _lever(erreur: type[Exception]):
    def implementation(*_):
        raise erreur()

    return implementation


def _brancher_utilisateur(
    monkeypatch: pytest.MonkeyPatch, utilisateur: User | None
) -> None:
    """Remplace le depot lu par `get_current_user`."""

    class FauxUserRepository:
        def __init__(self, db):
            self.db = db

        def get(self, user_id: UUID) -> User | None:
            if utilisateur is not None and utilisateur.id == user_id:
                return utilisateur
            return None

    monkeypatch.setattr(
        dependencies_module, "UserRepository", FauxUserRepository
    )


def _utilisateur() -> User:
    return User(
        id=IDENTIFIANT,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        username="ada",
        date_of_birth=None,
        postal_code=None,
        password_hash="pbkdf2_sha256$200000$aa$bb",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _en_tete_bearer(jeton: str) -> dict:
    return {"Authorization": f"Bearer {jeton}"}


def test_login_reussi_renvoie_les_jetons(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    _brancher_service(monkeypatch, login=lambda _: JETONS)

    reponse = client.post(URL_LOGIN, json=CORPS_LOGIN)

    assert reponse.status_code == 200
    assert reponse.json() == {
        "access_token": "acces",
        "refresh_token": "rafraichissement",
        "token_type": "bearer",
        "expires_in": 900,
    }


def test_les_jetons_ne_sont_jamais_mis_en_cache(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    _brancher_service(
        monkeypatch, login=lambda _: JETONS, refresh=lambda *_: JETONS
    )

    connexion = client.post(URL_LOGIN, json=CORPS_LOGIN)
    rafraichissement = client.post(
        URL_REFRESH,
        json={"refresh_token": "r", "device_info": "device-1"},
    )

    assert connexion.headers["cache-control"] == "no-store"
    assert rafraichissement.headers["cache-control"] == "no-store"


def test_le_service_recoit_l_email_normalise(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    recus = []

    def login(payload):
        recus.append(payload)
        return JETONS

    _brancher_service(monkeypatch, login=login)

    client.post(
        URL_LOGIN,
        json={
            "email": "  ADA@Example.COM ",
            "mot_de_passe": "x",
            "device_info": "device-1",
        },
    )

    assert recus[0].email == "ada@example.com"


def test_le_service_recoit_l_appareil(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    recus = []

    def login(payload):
        recus.append(payload)
        return JETONS

    _brancher_service(monkeypatch, login=login)

    client.post(
        URL_LOGIN,
        json={
            **CORPS_LOGIN,
            "device_info": "android",
        },
    )

    assert recus[0].device_info == "android"


def test_des_identifiants_invalides_renvoient_401(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    _brancher_service(monkeypatch, login=_lever(InvalidCredentialsError))

    reponse = client.post(URL_LOGIN, json=CORPS_LOGIN)

    assert reponse.status_code == 401
    assert reponse.json()["detail"] == "Email ou mot de passe incorrect."
    assert reponse.headers["www-authenticate"] == "Bearer"


def test_un_login_sans_corps_renvoie_422(client: TestClient):
    assert client.post(URL_LOGIN, json={}).status_code == 422


def test_refresh_reussi_renvoie_de_nouveaux_jetons(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    recus = []

    def refresh(refresh_token: str, device_info: str):
        recus.append((refresh_token, device_info))
        return JETONS

    _brancher_service(monkeypatch, refresh=refresh)

    reponse = client.post(
        URL_REFRESH,
        json={"refresh_token": "ancien", "device_info": "device-1"},
    )

    assert reponse.status_code == 200
    assert reponse.json()["refresh_token"] == "rafraichissement"
    assert recus == [("ancien", "device-1")]


def test_refresh_transmet_l_appareil_au_service(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    recus = []

    def refresh(refresh_token: str, device_info: str | None = None):
        recus.append((refresh_token, device_info))
        return JETONS

    _brancher_service(monkeypatch, refresh=refresh)

    client.post(
        URL_REFRESH,
        json={
            "refresh_token": "ancien",
            "device_info": "ios",
        },
    )

    assert recus == [("ancien", "ios")]


def test_un_refresh_invalide_renvoie_401(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    _brancher_service(monkeypatch, refresh=_lever(InvalidRefreshTokenError))

    reponse = client.post(
        URL_REFRESH,
        json={"refresh_token": "revoque", "device_info": "device-1"},
    )

    assert reponse.status_code == 401
    assert (
        reponse.json()["detail"]
        == "Session expirée. Veuillez vous reconnecter."
    )
    assert reponse.headers["www-authenticate"] == "Bearer"


def test_logout_renvoie_204_sans_corps(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    recus = []
    _brancher_service(monkeypatch, logout=recus.append)

    reponse = client.post(URL_LOGOUT, json={"refresh_token": "courant"})

    assert reponse.status_code == 204
    assert reponse.content == b""
    assert recus == ["courant"]


@pytest.mark.parametrize(
    "en_tetes",
    [
        pytest.param({}, id="sans-en-tete"),
        pytest.param({"Authorization": "Basic YWRhOm1kcA=="}, id="autre-schema"),
        pytest.param(_en_tete_bearer("pas-un-jwt"), id="jeton-malforme"),
    ],
)
def test_me_sans_jeton_valide_renvoie_401(client: TestClient, en_tetes: dict):
    """401 et non 403 : le client sait qu'il doit rafraichir sa session."""
    reponse = client.get(URL_ME, headers=en_tetes)

    assert reponse.status_code == 401
    assert reponse.json()["detail"] == "Session expirée ou invalide."
    assert reponse.headers["www-authenticate"] == "Bearer"


def test_me_renvoie_l_utilisateur_du_jeton(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    _brancher_utilisateur(monkeypatch, _utilisateur())

    reponse = client.get(
        URL_ME, headers=_en_tete_bearer(create_access_token(IDENTIFIANT))
    )

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["id"] == str(IDENTIFIANT)
    assert corps["email"] == "ada@example.com"
    assert "password_hash" not in corps


def test_me_pour_un_utilisateur_disparu_renvoie_401(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    _brancher_utilisateur(monkeypatch, None)

    reponse = client.get(
        URL_ME, headers=_en_tete_bearer(create_access_token(IDENTIFIANT))
    )

    assert reponse.status_code == 401


def test_les_routes_de_session_sont_montees_sous_le_prefixe_api(
    client: TestClient,
):
    assert client.post("/auth/login", json=CORPS_LOGIN).status_code == 404
